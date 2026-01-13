# New Site. New Domain. New Technologies

**Date:** November 22, 2015  
**Author:** Eugene Petrenko  
**Tags:** docker, jekyll, domain, virtual-environment, weekend

---

Some days ago I realized it's possible to have mostly any web site 
that is running behind [GitHub pages](https://pages.github.com).
Finally I decided to update my current blog and to have a site on domain root. 

First of I started with [Jekyll](https://jekyllrb.com/) instructions. 
There were a number of tricks and recommendation 
on GitHub on how to get it running in GitHub compatible way. I decided to
have *setup-as-a-code*, to avoid complicated and no-repeatable configuration steps.
I found [jekyll docker](https://github.com/jekyll/docker)
and started using it on Mac OS. To run docker is used 
[Docker Machine](https://docs.docker.com/machine/)
The only trick were to open extra port in Virtual Box, and to docker-machine's IP address to open site preview.
[This](https://github.com/jonnyzzz/jonnyzzz.com.jekyll/blob/master/jekyll.sh) is the script I use to run 
the container.

Sample site was created. [CNAME](https://help.github.com/articles/adding-a-cname-file-to-your-repository)
was added. DNS was updated. 

Initially I created a repository called `jonnyzzz.github.io` and `master` branch. Next I changed it 
to `jonnyzzz.com` and put the site into `gh-pages` branch. The second option looks better to me as I have 
several domains.

I used [jekyll-import](http://import.jekyllrb.com/docs/blogger) to import my older blog posts
from Blogger.com. It was quite easy to run in my jekyll docker container. But I lost code formatting
in imported posts. Re-formatted snippets manually. 

Next I was looking for a suitable theme for jekyll pages. It was 
[so-simple-theme](https://github.com/mmistakes/so-simple-theme)
that I used and tuned. I event forked theme repository to have a change to 
apply there updates to my pages. 

Next I added cookie policy warning via [Silktide](http://silktide.com/cookieconsent). 
Really simple to use and it works well

Created favicons via [http://www.favicon-generator.org/](http://www.favicon-generator.org). Had to install 
Gimp via Homebrew to crop avatar image.

I uploaded sources to `gh-pages` and it failed inside GitHub pages jekyll run. With only a 
notification that it failed. No logs or hints were there from GitHub error. I gave it up. 
 
I moved sources to `master` branch and made `_site` folder (a default generator output folder) to be 
another checkout repo checkout of `gh-pages` branch. Now I commit sources and generated site together. 
I also added `.nojekyll` file to site, to make sure GitHub's jekyll is disabled.

Hadi [wrote](http://hadihariri.com/2014/01/04/using-webstorm-to-maintain-a-jekyll-site) a 
guide on how to write Jekyll posts. I followed it and start using [WebStorm](https://www.jetbrains.com/webstorm/).
So now I have two VCS Roots in the project to commit to. The `_site` is updated automatically via running `jekyll server` in Docker. 

HTTPS is implemented via [cloudflare.com](https://www.cloudflare.com/). It was easy to install 
and nice to use. But you'll need to change domain name servers to CloudFlare's.

Finally, I created yet another stub site to implement redirect from `jonnyzzz.name`. In some weeks
I'll create similar redirect from `blog.jonnyzzz.name` too.
  
Now I can author posts in Markdown. I like it! Welcome to the new site and blog.