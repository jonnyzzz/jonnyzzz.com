# A Gradle Plugin to Detect Package Conflicts for Migration to Java 9 Modules

**Date:** October 18, 2017  
**Author:** Eugene Petrenko  
**Tags:** gradle, java, jigsaw, java9, modules, opensource, plugin, java9c, kotlin

---

helps to detect problems with split packages prior to the migration

It was an amazing journey to the [JavaOne](https://www.oracle.com/javaone/index.html) this year. 
There I had a great chance to [present](https://www.youtube.com/watch?v=UNg9lmk60sg&feature=youtu.be&t=6903) 
some features of [IntelliJ IDEA](https://www.jetbrains.com/idea) on the huge 
[stage](../../../../../talks/). I liked it. I was also amazed by the backstage processes. So many people are involved in there.

During those crazy times, I realized there is a problem for anyone willing to switch to Java 
modules. The problem is in packages. Every package is now allowed to be used only in 
one entry in the module path. It is still ok if you're on classpath. For more information, 
you may consider [project jigsaw](http://openjdk.java.net/projects/jigsaw/), 
[JEP 261](http://openjdk.java.net/jeps/261),
[AvoidConcealedPackageConflicts](http://openjdk.java.net/projects/jigsaw/spec/issues/#AvoidConcealedPackageConflicts), 
[Split Packages](https://blog.codefx.org/java/java-9-migration-guide/#Split-Packages)

The first step in the migration to modules is to make sure there are no package name clashes 
between files. The best way to know that for sure is to have a tool that analyze 
classpath for conflicts. So I created the plugin for Gradle.

Usage is pretty simple.

{% highlight groovy %}{% raw %}
plugins {
 id 'org.jonnyzzz.java9c' version '0.2.1'  /// Mind the updates!
}
{% endraw %}{% endhighlight %}

Once the plugin is applied, it adds the `java9c` task. The task itself depends on several generated tasks for 
every source set, e.g., `main` or `test`. `java9c` task, prints out the detected package conflicts for each source set.

For the demonstration, I created a tiny project that has classes in the junit's main package. The report looks like that:

![java9c task out example image]({{ site.real_url }}/images/posts/2017-10-18-task-output.png)

For multiple project Gradle projects, you may include the plugin in the following way, or, alternatively, 
you may select only specific projects to check.

{% highlight groovy %}{% raw %}
plugins {
 id 'org.jonnyzzz.java9c' version '0.2.1'  /// Mind the updates!
}

subprojects {
  apply plugin: 'org.jonnyzzz.java9c'
}

{% endraw %}{% endhighlight %}

The plugin is open source. You may find sources on [GitHub](https://github.com/jonnyzzz/gradle-java9c).

It is so easy to create so many different features. This time I decided to create a feature-poor plugin. 
Meanwhile, I reserved the `java9c` extension in Gradle for future features for the plugin.
Let me know if there is something I missed. Also, you may create a pull 
request [here](https://github.com/jonnyzzz/gradle-java9c).  

Sources & Binaries
==================

Sources are on [GitHub](https://github.com/jonnyzzz/gradle-java9c)

Plugin page on [Gradle Plugins](https://plugins.gradle.org/plugin/org.jonnyzzz.java9c)

The plugin is implemented in pure [kotlin](https://kotlinlang.org)

Have fun! And let me know if it helps.