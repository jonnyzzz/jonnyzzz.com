# Nodejs Builds

**Date:** January 28, 2019  
**Author:** Eugene Petrenko  
**Tags:** docker, javascript, nodejs, webpack, build

---

A build script to build a client-side web application in Docker


It was a challenge. I decided to try to create a web page to demo my HTTP API endpoint. I set myself a goal:
if I do a prototype in 1 hour - I'll have it for my project. I made it in 1.5 hours thou. 
It will be another story, how I made it deployed (and it include AWS, Terraform, and gotchas). This time,
let's focus on Node and NPM.

## Backgrounds

The best for a hackathon like projects, when the time is limited, it to get the goal done. 
Surprise, it is not always the super-duper technology, or programming language. 
For me it was obvious - I need to make the site to demo the API endpoint.
Technology stack is up to me.

The time is limited. Pick a technology you know the best. Pick an option, you most
confident with. It is tricky, again, it should be technology that makes *goals* achievable 
faster. It is not the technology you know, but you cannot make it. 

I'm not a web developer professional. I had nothing to pick from. 

Ask an expert if you are doubts. [Andrey](https://www.linkedin.com/in/andrey-skladchikov-94336416a)
suggested using [Ring UI](https://jetbrains.github.io/ring-ui/master/index.html)
library. Right now I'm happy I decided using the library. Frankly, I like the way [React](https://reactjs.org)
approaches to web pages. 

The best part - Ring UI comes with the generator, the generator generates an alive skeleton
for the website. Now one can start, debug, and build the site. That is it. Of course,
[Node JS](https://nodejs.org) is required on the machine. Awesome! I use [IntelliJ IDEA](https://jetbrains.com/idea)
with the [Node JS Plugin](https://plugins.jetbrains.com/plugin/6098-nodejs) to develop it. 

## Building

Back from the old days, I remember how painful it can be to build a web site
if you do not have right tooling on your machine. One needs similar tooling for
the CI builds too!

So I wrote few bash scripts to automate it for me. I use Docker image with Node JS. It helps a lot!

### Dockerfile

The `Dockerfile`:

```dockerfile
FROM node:11

RUN apt-get update && apt-get install -y rsync

RUN mkdir /build /build-src

COPY package.json package-lock.json /build/
RUN cd /build && npm install
``` 

All we need to build the project - is an environment with Node, NPM and warm `node_modules`. Let's do it!
The `Dockerfile` uses `node:11` as the base image to have Node and NPM. Next, we add current `package.json`
to install `node_modules`. Now `node_modules` and NPM caches are pre-packed into the container!

### Building

As you see from the `Dockerfile`, we have `node_modules` created in the `/build/` folder. Now we need
project sources to be in the folder to run the true build. We must not mix `node_modules` from the 
host computer with `node_modules` from our Docker container. The fact is, you may have OS-specific binaries
under `node_modules`, and it may not play nice if you mix them.

We mount original project sources under `/build-src/` folder in docker. We assume the build will
share the compiled site into `/build-dist/` folder. I use the following script to make it. 

The `build-container.sh`:
```bash
#!/bin/bash
set -e -x -u


## copy sources into the right folder
rsync -ai --delete --progress /build-src/ /build/ --exclude node_modules

## do the build
cd /build
npm run build

## copy results back
rsync -ai --delete --progress /build/dist/  /build-dist/

```

### Running in the Container

Let's start the build in the container. For that, I have the following script.

`build.sh`

```bash
#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
set -e -x -u

IMAGE=project-node-js

docker build --tag ${IMAGE} .

ROOT="$(cd $DIR && pwd)"
DIST="${ROOT}/dist"

rm -rf ${DIST}

docker run -it --rm \
     -v ${ROOT}:/build-src:ro \
     -v ${DIST}:/build-dist \
     ${IMAGE} /build-src/build-container.sh
```

You also need to add the host `node_modules` to the `.dockerignore` file. It will make `docker build` command
to run faster.  

The first step - we build the docker container from the `Dockerfile`. Docker does incremental
builds for us. A change in `package.json` will trigger the container rebuild. Without changes in `package.json`,
it will do nothing pretty fast.

The second step - we run the build in the container. 

It may be necessary to fix permissions of the files, that you have under the `${DIST}` folder on Linux.
That is not needed for builds on Mac, and I assume on Windows.

## Conclusion

Now I have a build script for my project. One needs only Docker to build the project. It is essential,
the version of Node is hard-coded in the build scripts, we will need to changes to the environment what it
changes. The CI builds simplified too! We have no duplication between local builds and CI builds. 
Everyone calls the same `build.sh` file to make it. 

Do you like to try that? Here is a small exercise for you - add the development web server support into the scripts. 
I'll be happy to see your code and update that post.