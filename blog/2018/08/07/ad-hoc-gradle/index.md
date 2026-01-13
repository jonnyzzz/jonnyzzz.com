# Ad-hoc Plugins with Gradle

**Date:** August 07, 2018  
**Author:** Eugene Petrenko  
**Tags:** gradle, java, groovy, plugin, gradle-plugin, build, dependencies

---

Gradle code reuse on steroids.


There are many ways to reuse code in [Gradle](https://gradle.org) builds. The 
major and the most powerful one is
to write a Gradle plugin either as an independent project or inside `buildSrc`. 
You may want to check official documentation
[here](https://docs.gradle.org/current/userguide/plugins.html).
All of these approaches require additional efforts from both the development and the infrastructure sides.
Will you and your team be happy of you doing that?
 
I want to share the short-cut to make code reuse without too much work.
I will consider a
[Multi-Project Gradle builds](https://docs.gradle.org/current/userguide/multi_project_builds.html).
It makes less to no sense for a Single Project Gradle builds, there is nothing to reuse, generally.

What Gradle code to reuse? There are a plenty of places for it. The most trivial is
dependencies. You'd like to try using the same versions of libraries along the sub-projects.
Repositories, packaging, testing, plugins, configurations are the places of reuse too. Yet another
example is Kotlin plugin or Scala plugin configuration. 

## Subprojects

The most standard feature in Gradle builds. 
`subprojects` is the 
[block](https://docs.gradle.org/current/userguide/multi_project_builds.html#sec:subproject_configuration)
where you apply the same code snippet to all child (any level)
projects.

Projects in Gradle forms a tree structure, it replicates the filesystem. 
A *parent* project in Gradle is the project that is in the parent folder 
of a child project folder. The `build.gradle` is optional and you are not obliged to
have one. For example,
the line `include ':a:b:c:d'` from a `settings.gradle` file 
defines the following child projects: `a`, `b`, `c` and `d`.

I like to use `subprojects { .... } ` block in parent projects to configure 
common stuff, like dependencies, plugins, repositories. Let's see the example:

```gradle
subprojects {
    repositories {
        jcenter()
        mavenCentral()
    }
 
    dependencies {
        compile "org.slf4j:slf4j-api:1.7.25"
        testCompile "junit:junit:4.12"
    }   
}        
```

Here I set up the default maven repositories in all child projects.
Also, I include the standard dependencies, namely, [SLF4J](https://www.slf4j.org/) and
[JUnit4](https://junit.org/junit4/). The configuration of
[JUnit5](https://junit.org/junit5/docs/current/user-guide/) is yet
another great example to share Gradle code between projects.

It is possible that one does not want to configure all child projects,
but some projects only. It is possible. But, It'd be better to move that
project somewhere instead. I use the following,
`configure(project(':a'), project('b').subprojects) { .... }` to 
apply the same settings to several projects only.

## Apply From File 

The next way to apply common configuration is to use `apply: from: file(...foo.gradle)` syntax.
You move the configuration to a dedicated file somewhere in the project. You
include the file to every project, where you need it. 
 
That is the way to re-include the same part of your Gradle script into many
projects. The only problem here is that the `build.gradle` and the `...foo.gradle` 
are executed in an isolated environment. It might be hard to pass parameters
back and forth.

## A Common Plugin

The most generic approach is to create a Gradle plugin or a custom task. 
There is the [documentation](https://docs.gradle.org/current/userguide/plugins.html) page.
Let's see, how to try writing a plugin just in our `.gradle` files. 

I use [IntelliJ IDEA](https://jetbrains.com/idea) to navigate to interfaces and javadocs.
It helps me a lot with code completion and error highlighting
directly in `.gradle` files, which actually use Groovy.

Gradle allows declaring classes in `.gradle` files. That is the way to
create an ad-hoc plugin just in a parent project. You should know, that you 
will not be able to see the created class outside the `.gradle` file, where
you created it. The good part is that you may still use `subprojects` and write the following:

```gradle

subprojects {
  apply plugin: MyPluginClass
}

class MyPluginClass implements Plugin<Project> {
  @Override
  public void apply(Project project) {
    ...
  }
}
```

That is the most trivial way to create you own Gradle plugin and to enable it 
for all child projects. It does not require one to invest into infrastructure 
(e.g. deployment of a plugin, build configurations and so on). 

You may use `org.gradle.api.plugins.ExtensionContainer#create(...)`
function to add your own Gradle DSL
[extension](https://docs.gradle.org/current/userguide/custom_plugins.html#sec:mapping_extension_properties_to_task_properties).
That is the standard way to include parameters from the plugin usages. 

## Ext Block

What if I need to apply the ad-hoc plugin only to some selected sub-projects? And I do not
like to code it in the parent project `build.gradle`. Similarly, I may want to reuse some dependencies
especially for selected projects. 

The `ext { .. }` [block](https://docs.gradle.org/current/userguide/writing_build_scripts.html#sec:declaring_variables)
in Gradle is for me. I combine it with the `subprojects { .. }` block.
[Closure](http://groovy-lang.org/closures.html) (or Lambda) is a possible value of a
property from `ext` block too.
Let's combine those features to level-up the code-reuse in our Gradle script. First, in 
a parent project we add the code:

```gradle
subprojects {
  ext {
    dep_arrow = {Project project ->
      project.dependencies {
        compile "io.arrow-kt:arrow-core:0.6.1"
        compile "io.arrow-kt:arrow-typeclasses:0.6.1"
        compile "io.arrow-kt:arrow-data:0.6.1"
    }
  }  
}
```

Then in a selected child project I simply enable [Arrow](https://arrow-kt.io/) library by
writing the only one line:
```gradle
ext.dep_arrow(project)
```

Theoretically, It should work with an implicitly captured Project in Closures, without `Project` parameter, e.g.
`dep_arrow = { dependencies { ... } }`. I was lazy to try that.

The similar trick helps to enable ad-hoc Gradle plugins too. 

# The Use Case

I work on an project, where we decided to use micro-services. Technically, it
means, we split the whole code base into the set of small executables. 
The same language, namely Kotlin/JVM, is used to implement all services. There are common things one need 
to have for every service, for example, it includes logging configuration, communication
setup, crashes handling. I need the only way to pack those services too. 

What did I do? At first, I use [Application plugin](https://docs.gradle.org/current/userguide/application_plugin.html)
to implement the executable. It executes the same entry-point class. The entry-point class
finds the micro-service class to start it. I plan to use the [jib](https://github.com/GoogleContainerTools/jib) plugin
to wrap my services into Docker images.

From the Gradle side of things. I created scripts for one service manually. Then, I turned that code into an ad-hoc
Gradle plugin. I enabled the plugin explicitly in the service projects.
The plugin configures the Application plugin, adds dependencies, adds
an [extension](https://docs.gradle.org/current/userguide/custom_plugins.html#sec:mapping_extension_properties_to_task_properties)
to get service-specific parameters.

Right now, the service is created with only a few Gradle lines:
```gradle
ext.micro_service(project)

micro_service {
    entryClassName = '<THE ENTRY POINT CLASS OF THE SERVICE>'
}
``` 

Let your builds be simply. Feed free to ask me for details in the comments below. 
There is also the official [documentation](https://docs.gradle.org/current) for Gradle.