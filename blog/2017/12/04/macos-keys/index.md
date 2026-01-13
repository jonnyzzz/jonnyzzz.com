# MacBook Fix Tilde Key

**Date:** December 04, 2017  
**Author:** Eugene Petrenko  
**Tags:** mac, macOS, keys

---

A tiny trick to remap keys on macOS X


Recently I switched from an EN-US MacBook Pro Keyboard to a DE keyboard. Suddenly, I found
an unexpected problem with keys layout.

There are several differences in the layout. 
You may have a look to all possible keyboard layouts 
[here](https://keyshorts.com/blogs/blog/37615873-how-to-identify-macbook-keyboard-localization){:target="_blank"} 

The main difference is that in EU version of the keyboard we have additional
buttons, Enter key is vertical, Left Shift key is shorted to give a room for 
an extra key. 

The problem is as follows: `tilde` key is near `1` in the EN-US keyboard (and other PC keyboards),
while it is between Shift and Z in the EU keyboards.

Also, on Mac OS we use `CMD+tilde` to switch between windows on the same App. I have even
installed [Easy Window Switcher](https://neosmart.net/EasySwitch/){:target="_blank"} to have the same 
experience on Windows! 

It is hard for me to learn the trick. And it will not work correctly, if you remap a key. Namely,
in Russian keyboard layout the remapped shortcut will not work. Yeah! MacOS System shortcuts DO 
depend on keyboard layout. Sad story. 

I can across a tiny and nice article to remap keys on MacOS. 
[TN2450](https://developer.apple.com/library/content/technotes/tn2450/_index.html){:target="_blank"}

And the way to re-map keys is the following:

`
hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000064,"HIDKeyboardModifierMappingDst":0x700000035},{"HIDKeyboardModifierMappingSrc":0x700000035,"HIDKeyboardModifierMappingDst":0x700000064}]}'
`

That is all you need. Next you'd need to have a patched Russian keyboard to fix Ё character. For the fix I use 
[ukelele](http://scripts.sil.org/ukelele){:target="_blank"}

Anyway, you do not need to install ANY third-party apps to solve the key-remapping problems