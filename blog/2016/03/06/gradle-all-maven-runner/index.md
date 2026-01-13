# Using Gradle to download and run anything

**Date:** March 06, 2016  
**Author:** Eugene Petrenko  
**Tags:** gradle, maven, hint

---

There are so many small tasks that as solved via a tiny programs. Most of such programs 
are to call several libraries to have an end-result. In the JVM world, most of those 
libraries are downloadable from a maven repository.

It could be tricky in general to deliver dependencies for the script to run. There 
are several possible ways to solve it. 


I found an easy way to make Gradle download dependencies and run a script. 
This makes the scripting done with groovy too.

Here goes an example to run an Amazon API and wrap it as Gradle task:
{% highlight groovy %}{% raw %}
buildscript {
  repositories {
    jcenter();
  }
  dependencies {
    // List all dependencies for scripting here
    classpath 'com.amazonaws:aws-java-sdk:1.10.48'
  }
}

// Import what is necessay
import com.amazonaws.auth.profile.ProfileCredentialsProvider
import com.amazonaws.services.s3.AmazonS3Client

task runScriptForAmazon << {
  // The script source goes here!
  def s3client = new AmazonS3Client(new ProfileCredentialsProvider())
  println "Working with endpoint: $s3client.endpoint"
}
{% endraw %}{% endhighlight %}

The only trick here is that Gradle includes all script dependencies into classpath 
where tasks are loaded and executed. 

Even more, adding [Gradle Wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html) 
makes it runnable on eveny machine with JVM only. 
(A `Wrapper` task can be used to have Gradle generate wrapper scripts)

Happy scripting!