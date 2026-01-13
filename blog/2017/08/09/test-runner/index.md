# A Bash Test Runner for TeamCity

**Date:** August 09, 2017  
**Author:** Eugene Petrenko  
**Tags:** teamcity, test, testrunner, shell, bash, ci, go, build

---

An ad-hoc bash test runner with TeamCity support 

That time I was playing with a tiny [Go](https://golang.org) project. I was doing a console tool 
to update [Consul KV](https://www.consul.io/) in the required way, with transaction and domain specifics.
 
Why the tool? Well, I was needed to update several keys from our [Ansible](https://www.ansible.com/) deployment
scripts. And [transactions](https://www.consul.io/api/txn.html) were the nice way
to run an atomic update. Secondly, it is better to offload tricky domain specific code to a dedicated 
place, which has better tests and build process. The alternative in my case was to 
use `curl` or similar to run Consul KV transactions with no easy way to test it easily. 

By the time I realized it is better to call the tool from a command line to test it
does correct changed to the KV. So I was looking for a test runner. 

After some research, I decided to use 
[TeamCity Service Messages](https://confluence.jetbrains.com/display/TCD10/Build+Script+Interaction+with+TeamCity)
to report test progress back to the CI.

The idea of tests is as follows. Each test is created as an `.sh` file under `tests` folder. Exit code is used to tell 
a failure from success. That is necessary to be able to run every test and only one test locally while developing.

Finally, I created the following test runner:

{% highlight bash %}{% raw %}
#!/bin/bash
set -e -x -u
cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Running integration tests..."
FAILED=0
TC=##teamcity
echo " ${TC}[testSuiteStarted name='integration-tests'] "

for TEST in tests/* ; do
  TEST_NAME=$(basename $TEST)
  echo " ${TC}[testStarted name='$TEST_NAME' captureStandardOutput='true'] "
  ./$TEST || {
    echo " ${TC}[testFailed name='$TEST_NAME'] "
  }
  echo " ${TC}[testFinished name='$TEST_NAME'] "
done

echo " ${TC}[testSuiteFinished name='integration-tests'] "
{% endraw %}{% endhighlight %}


By the time, I'm still uncertain, if I need to use this one. Or, maybe I should switch to `go test` in the future. 
The best feature of the test above is it supported by [TeamCity](https://jetbrains.com/teamcity).

Yoy may find the actual version of it on GitHub. 
[https://github.com/jonnyzzz/teamcity-test-script](https://github.com/jonnyzzz/teamcity-test-script).

UPD. I have re-evaluated approaches and decided to implement integration tests with 
[go test](https://golang.org/pkg/testing/) instead. The main problem was that I need to pass many 
parameters to my tool to start it in a test. Hard-coding those parameters for every test was not worth it. 
In Go it was easier to create an assertions API to check Consul KV state too. The API helps to setup 
necessary KV state too. The whole approach makes it simpler to write tests.

I'm able to run all of my tests from [Gogland](https://www.jetbrains.com/go/). 
The test assumes Consul is running by checking a particular file under the `GOPATH`. 
There is a setup bash script that downloads and starts Consul dev server both for development and continuous integration. 
I extended the [bash script]({% post_url blog/2017-07-05-go-build %}) for that.