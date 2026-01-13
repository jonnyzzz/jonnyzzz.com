# Celebrating 20 Years at JetBrains: A Journey from Junior Developer to Department Lead

**Date:** September 17, 2024  
**Author:** Eugene Petrenko  
**Tags:** kotlin, intellij, jetbrains, jvm, talks, job

---

This month marks my 20th anniversary at JetBrains -- a journey that has taken me from a student developer to leading the IDE Services department. It's been an incredible ride filled with learning, growth, and collaboration with some of the brightest minds in the industry.

## Early Days and Growth

I began my career at JetBrains working on **ReSharper** around version 2.0 in 2004, 
experimenting with **F# support** and later developing a **C# 2.0 to C# 1.1 converter**.
Those early years were all about exploration and honing my skills in software development. 
I remember coding the “invert if” quickfix, type hierarchy, and the about dialog.

After some time, I transitioned to the **TeamCity** team, where I spent about eight years. During this period,
I contributed to many parts of the product, including:
* .NET build runners support.
* Worked on core components and support for multiple build runners.
* Developed typed parameters and improved the plugin infrastructure.
* Enhanced the build agent and added cloud support with Amazon AWS.
* Implemented NuGet support in TeamCity.

I also authored several now-deprecated open-source plugins, that enhanced the platform's functionality and flexibility:
* TeamCity.GitHub
* TeamCity.Node
* TeamCity.Virtual

Following my time with TeamCity, I moved to the **Upsource** team (a part of Ring), where I leveraged TeamCity's version control integrations to power Upsource, our code review tool that works with Git, Subversion, Perforce, and other version controls. The next chapter of my work was implementing the **Git Hosting** project for the company and the market. While the project presented challenges, it eventually evolved to empower **JetBrains Space**.

## Embracing the Community

I learned much attending conferences and speaking with people there. Attending conferences like **NDC Oslo**, **Devoxx Belgium**, **JavaZone**, and **JavaOne** sparked a dream to share my own ideas on stage. It took me some time to decide –- I was initially shy about applying to speak. If you're interested in presenting at conferences, my advice is to start by submitting proposals, even to local meetups.

It was great fun to play with early bits of JetBrains' own programming language -- [Kotlin](https://kotlinlang.org). I created my first public TeamCity plugin [back in 2013]({% post_url blog/2013-01-14-kotlin-nodejs-and-teamcity %}), years before the Kotlin 1.0 release.

I eventually gave my first talk at the [**Gradle Summit** in 2016](https://jonnyzzz.com/talks/2016-06-22-gradle-summit/). This experience was transformative, teaching me the value of stepping out of my comfort zone. Being a speaker was a long-held dream, and my speaking career primarily revolved around early **Kotlin**. To date, I have 42 talks in my [portfolio](https://jonnyzzz.com/talks/) including
[Kotlin DSLs in 42 Minutes](https://jonnyzzz.com/talks/2017-10-22-devoxx/), a keynote, and workshops in Australia. I also had been co-organizing [Kotlin User Group meetups](https://www.meetup.com/Kotlin-User-Group-Munich/?eventOrigin=home_groups_you_organize). I'm grateful to **Enrique López Mañas** for that opportunity. If you are in Munich and interested in Kotlin, join us!

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">&quot;Don&#39;t trust anybody. Don&#39;t trust me. Trust your profiler&quot; - <a href="https://twitter.com/jonnyzzz?ref_src=twsrc%5Etfw">@jonnyzzz</a> at <a href="https://twitter.com/kotliners?ref_src=twsrc%5Etfw">@kotliners</a> <a href="https://twitter.com/hashtag/Kotliners?src=hash&amp;ref_src=twsrc%5Etfw">#Kotliners</a> <a href="https://t.co/HDCRwShsjl">pic.twitter.com/HDCRwShsjl</a></p>&mdash; Guillermo Orellana (@wiyarmir) <a href="https://twitter.com/wiyarmir/status/1136898792068976640?ref_src=twsrc%5Etfw">June 7, 2019</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

I've had the privilege of working with amazing people, listening and sharing stages with industry leaders. For instance, at the **JavaOne 2017** keynote, I shared the stage with **Mark Reinhold** to demo IntelliJ IDEA's support [for Java Modules in Java 9](https://jonnyzzz.com/talks/2016-09-22-javaone/)

![Eugene At JavaOne]({{ site.real_url }}/images/posts/2024-09-17-eugene-at-javaone-2017.jpg)

## A Leap into Advocacy

When **Hadi Hariri** offered me a position on the **Kotlin Advocacy** team in 2018, I embraced the chance to focus fully on and learn non-developer topics like public speaking, writing, and community building. Although it was hard to step away from the Git Hosting project, which I had been working on, this move significantly broadened my horizons. 

Becoming a developer advocate in such an awesome team was a great decision. After gaining valuable experience, I returned to development with newfound insights. The lessons and skills I acquired made me more capable of handling complex projects. 

Around that time, in early 2019, **Maxim Mosienko** introduced me to Coursera's [Leading People and Teams specialization](https://www.coursera.org/account/accomplishments/specialization/4FG6YF6DQGHD). Completing this course was eye-opening, allowing me to see the world from a different angle and enhancing my leadership abilities.

## Innovating with the Toolbox App

In parallel with these career changes, I participated in a [**hackathon**](https://blog.jetbrains.com/blog/2016/10/18/jetbrains-toolbox-app-1-0/), where I had the chance to replace my home-grown scripts with an application to manage JetBrains' IDEs on my computer. The **Toolbox App** started as a multi-year 20% project that I worked on. There were no full-time developers on the project; we used **Qt** and **C++**, later integrated the **Chromium Embedded Framework (CEF)**, and later transitioned to the **JVM**. Now this project uses JetBrains Compose Multiplatform framework https://www.jetbrains.com/lp/compose-multiplatform/.

The Toolbox App was released in 2016 and surprisingly became the backbone of my future career changes. For me, it was great to take part in developing this project, and I'm still closely involved with it. I remember my long evenings spent coding in Qt C++. You can listen to **Victor Kropp**'s talks to learn more about the project and its evolution.

![Toolbox App 1.0](https://blog.jetbrains.com/wp-content/uploads/2016/10/toolbox_preview.gif)

## Leading Innovations

Returning to development, I took on new challenges within the **IntelliJ IDEA** team under the guidance of **Dmitry Jemerov** and **Konstantin Bulenkov**. I created the **JDK download feature** in IntelliJ IDEA, simplifying the user experience by allowing developers to download and configure the JDK directly from the IDE. This was a highlight during the product's 20th anniversary.
See how this feature is promoting every JDK release out there!

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">You can download Java 23 right inside your <a href="https://twitter.com/hashtag/IntelliJIDEA?src=hash&amp;ref_src=twsrc%5Etfw">#IntelliJIDEA</a>! <a href="https://t.co/yxceDU7ec3">https://t.co/yxceDU7ec3</a> <a href="https://t.co/g5y0H0UNtZ">pic.twitter.com/g5y0H0UNtZ</a></p>&mdash; Tagir Valeev (@tagir_valeev) <a href="https://twitter.com/tagir_valeev/status/1836068303850074456?ref_src=twsrc%5Etfw">September 17, 2024</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

The next project was **Shared Indexes**, which was to reduce the indexing time on the large codebases. We made it from an internal experiment to [a public feature](https://www.youtube.com/watch?v=xJKff0QUd3c).
It was a challenging project for me where I had a chance to shape this product,
promote it inside and outside the company. We even spoke to customers to receive the feedback.
Looking back, I see areas where we could have enhanced the project,
and I'm eager to revisit it in the future.

## Engaging with Customers

During that time with Shared Indexes, we also began speaking directly with IntelliJ IDEA customers. It was eye-opening, and I learned how our features are used in real-world scenarios. In parallel, **Alexander Podkhaliuzin** started the Customer Success Engineering initiative.

Understanding customer requests and challenges became the foundation for starting **Toolbox Enterprise** -- a product designed to manage IDEs at a company scale. Alexander, **Yuri Artomonov**, and I were at the inception of this project, and we leveraged the Toolbox App, weaving together several threads of my previous work. It was so exciting to speak and demo the product to
our first pilot customer.

We tested the B2B market of the Toolbox Enterprise project. It appeared clear that license management and other features are the great add-ons to the project. **Kirill Skrygan** proposed the idea to expand the scope of the product and to reshape the suite for the wider B2B audience. That was how
[JetBrains **IDE Services**](https://www.jetbrains.com/ide-services/)
was born as the expansion and evolution to the Toolbox Enterprise. This transition was supporting and stimulating my further growth and development. I'd like to thank **Vitaly Gordeev** for his support and mentorship throughout my journey and to this day.

> "Great things in business are never done by one person; they're done by a team of people." — Steve Jobs

Starting with Toolbox Enterprise, my role shifted from software development to management, leadership, and product development.
I've learned that great things are more achievable with a team of people. We started as a small team, 
and together we delivered the very first iterations of Toolbox Enterprise to our pilot customers-companies. As the team grew, we introduced sub-teams to manage our department more effectively. Even with all we've accomplished, there's still so much more we can do, learn, and improve within our department. There are many great achievements ahead of us.

## Current Endeavors

Now, I lead the [**IDE Services** department](https://linkedin.com/in/jonnyzzz). We're dedicated to enhancing developer experiences and delivering solutions that drive productivity at a customer-company scale. This role also provides space for growth and continuous development, allowing me to tackle new challenges and drive the evolution of our products.

In the IDE Services department, we have the opportunity to provide an umbrella of products that help companies manage IDEs for hundreds of their developers. Starting from **AI Enterprise** product to offer Enterprise-tailored AI Assistant, through **Code With Me**, **IDE Provisioner**, and **License Vault**. We're not limiting our offerings to these products only -- stay tuned for more. Managing the department and its people has expanded my responsibilities and provided many opportunities to learn and grow. Just in case, we are hiring many various roles!

## Looking Back and Ahead

I moved to Germany back in 2011, and much of my development work has taken place here. Before Germany, I was studying at university, completed my diploma with distinction, and later defended my **PhD (Candidate of Sciences)** in 2009. After relocating, I decided to focus more on the industry.

## Join me in Celebrating

To mark this milestone, I'm hosting an **AMA (Ask Me Anything)** session on LinkedIn and on X (Twitter). Whether you're interested in product development, navigating career transitions, or discussing the future of developer tools, I invite you to join the conversation.

I'm grateful for the incredible journey so far and excited about what the future holds. Huge kudos to everyone who has been a part of my story—colleagues, mentors, and the amazing developer community. I am always surrounded by great people. Together, I know we can move mountains.

*Feel free to ask me anything or share your own experiences below!*

<blockquote class="twitter-tweet"><p lang="en" dir="ltr">Twenty (20) years at <a href="https://twitter.com/hashtag/JetBrains?src=hash&amp;ref_src=twsrc%5Etfw">#JetBrains</a>. Ask me anything! Like, Retweet, Comment! <a href="https://twitter.com/hashtag/AMA?src=hash&amp;ref_src=twsrc%5Etfw">#AMA</a></p>&mdash; Eugene Petrenko (@jonnyzzz) <a href="https://twitter.com/jonnyzzz/status/1835995363070861664?ref_src=twsrc%5Etfw">September 17, 2024</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>

<iframe src="https://www.linkedin.com/embed/feed/update/urn:li:share:7242052967049154561" height="242" width="504" frameborder="0" allowfullscreen="" title="Embedded post"></iframe>