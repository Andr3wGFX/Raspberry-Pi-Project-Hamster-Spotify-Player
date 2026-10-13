# Raspberry-Pi-Project-Hamster-Spotify-Player
This repo has my iterative process for my Raspberry Pi hamster photo booth and Spotify player project and how it progressed over time.

This took the better part of a month to make, and was something I did on the side for fun with leftover parts that my Beaver Works Summer Institute instructor gave me (Thanks for the lessons and the Pis :)). I can't count the total amount of hours I'd spent on this, but I'd guess something around 30 total or so, most of which was working on the code.

This side project currently runs on a Raspberry Pi 5, which connects to my home internet and uses it to access my Spotify feed. It's attached to a whiteboard that I've placed facing me on my desk so I can take notes and see what I'm playing at the same time. I also added the internals from an old webcam on top, which can take pictures of me, and through a Google Drive connection, I can upload photos directly to my drive. I installed a MediaPipe expression recognition algorithm on the Pi, which allowed me to match Hamster meme pictures to expressions and put them on top of faces live on the screen. I also have a timelapse feature that takes 30-minute timelapses, which helps keep me accountable while doing work and incentivizes me to take a quick break every 30 minutes (and helped me see how bad my posture while working was).

Here's how it looks, and where it is on my desk:
<img width="1388" height="925" alt="image" src="https://github.com/user-attachments/assets/844c2840-6af1-48b0-bf77-a4bfc34a1b22" />

<img width="1388" height="925" alt="image" src="https://github.com/user-attachments/assets/68f33890-2f24-49d0-9e0f-cab5a8092dd4" />


I reconstructed my build process in this read me file using my original notes from my build process. It has everything from what I did, how I was inspired by others, what parts I struggled with, and details of what changes I made as time went on to improve it.

<p>$\color{firebrick}\text{\bf Build Log:}$</p>

<p>$\color{cyan}\text{\bf September 2nd}$</p>

After getting back from Beaver Works, I decided that I'd use the Raspberry Pi 4 that my instructor had given me at the end of my course. I saw a Spotify deck on my Instagram home page and decided that it sounded like a fun thing to try and create using my Pi 4. At first, I didn't use my Pi 5, which was also from my instructor, since I thought that 8GB of RAM and the increased processing power would have been overkill for such a small project. This version connects to Spotify's API and tracks what songs I was listening to, and uses three buttons to let me skip and pause tracks.

<p>$\color{cyan}\text{\bf September 8th}$</p>

This was when I actually connected all my wires from the Pi 4 to a cheap 2-inch LCD from AliExpress (ST7789) and 3 buttons.

At this stage, I originally didn't know how to enclose this structure, since my Pi 4 was decently large compared to the Pico that the person from my inspo video had used; I couldn't make a small, clean box for my setup. Thus, I found an old whiteboard that I had lying around and decided to attach what I'd made to it, so I could take notes while being able to adjust my music at the same time. 

_Problems and how I fixed them at this stage:_
- Display issues: My display wouldn't actually show color and only had a backlight turn on. I tried many code-based diagnostic tests to try and fix this, taking about an hour trying to flash my display with color through several libraries and methods without success. Eventually, I realized I'd been a bit dumb while wiring and that I'd wasted an hour trying new libraries when the original one I'd tried was the right one, and I'd just mixed up two wires in my electrical process. Great reminder that the simplest explanation is most likely the one that's correct. (The setup after I finally fixed it is pictured below)
- My display was still running slowly at 4 MHz; however, for Spotify this was okay since it only needed an update every so often when I switched songs or paused the track.

<img width="650" height="623" alt="Fixed the display!" src="https://github.com/user-attachments/assets/4268020d-0b7d-4195-8902-c9a02de7d7c7" />

<p>$\color{cyan}\text{\bf September 9th - 13th}$</p>

This is when I decided to make my display prettier. I tried several backgrounds, including a dark color, a pastel gradient, and eventually settled on a blurred photo background. This was coupled with a new font that was more bubbly and fit my workspace better, and a wavy "snake" progress bar that was redrawn by sending only its own strip of the screen to save compute. I also added a nice photo slideshow for when I didn't have anything playing, and I added a script for photo conversion so that I could take any photo I had and make it into the correct formatting for my small 2-inch display. I also added a clock and weather overlay so I didn't have to rely on my computer screen for these things.

_Problems and how I fixed them at this stage:_ 
- The font I wanted to use only had a free demo available without the numbers, so I ended up using that font, coupled with numbers from another font
- The wavy snake progress bar looked choppy because of the refresh rate, which I fixed by changing my screen to a higher refresh rate after finding out through a diagnostic script that I could turn up the speed (full process in the next date entry)

The following photo is how it looked after I added these:
<img width="1388" height="925" alt="New UI!" src="https://github.com/user-attachments/assets/49c5bf54-8ee7-4eaf-9993-58784c7f68f6" />


<p>$\color{cyan}\text{\bf September 13th}$</p>

This was the day I realized I'd been wasting my display a bit. I was distraught at how slow the refresh rate was since I'd used 4 MHz, when it turns out my screen could work at 64 MHz. I figured this out because I'd gotten frustrated with how it looked, and then added a diagnostic script that flashed colored bars on the screen at varying rates, which is how I found out it could run at 64 MHz. That meant a full frame went from 307 ms to about 20 ms, which made the entire thing look smoother. 

I also found an old webcam in a drawer, which I decided to use. I kind of felt that using a whole Pi 4 for just a Spotify API was a waste of compute. Since I figured out my display could work at a faster refresh rate, a live camera view was actually possible, so I went ahead and connected my Pi to the internals of this old webcam (old casing seen below) and created a separate app that I could activate by holding the pause button on my Spotify Deck. This camera was then bolted to my whiteboard using a spare piece of plywood. That evening, I ended up creating a Google developer account for an app that I could use to upload photos directly to my Google Drive. The choice to add a camera was also partially inspired by the online challenge of taking a photo a day for an extended period of time so that one could see how they'd changed over time, which I thought could be made easier since I often do work at my desk and it could be the perfect opportunity for a repeated photo.

<img width="645" height="493" alt="Old casing of webcam that I used the internals of." src="https://github.com/user-attachments/assets/3bb9536e-4538-46e2-9d1a-61be7af530cd" />

Wiring at this stage (Don't mind the mess)
<img width="1388" height="925" alt="image" src="https://github.com/user-attachments/assets/19fd51f0-f498-4aeb-a1d7-f9ea7f7c61d6" />


<p>$\color{cyan}\text{\bf September 14th}$</p>

On this day, I decided that a simple camera wasn't enough. I'd seen a video by Catherine (an online creator) that used MediaPipe's expression system to match a hamster meme (pictured below) to a person's face based on their expression. I used her app as a reference for how I could try to do it myself, but ended up not being able to use MediaPipe on my Pi 4 because its processor doesn't have the instruction set that MediaPipe needs to run. So I ended up creating something new that used older OpenCV face detection with three detectable moods using 68 facial tracking points. It wasn't as accurate as her version for the facial expressions, but it did allow me to run it on my existing hardware. I also expanded on what she'd made by making an OpenCV filter find the eyes of the person, measure the distance between them, and then track their face live using the camera and tacking on a hamster sticker, scaled with their eye distance. I also made it work for as many people as could fit in frame by making a system for handling multiple faces, which her version lacked.

<img width="1000" height="1170" alt="image" src="https://github.com/user-attachments/assets/ea3fbf04-60b6-42f3-87ff-de396c281ce2" />


_Problems and how I fixed them at this stage:_ 
- My face filter ended up updating slowly, which turned out to be an issue with how I processed my expressions every few frames. I fixed this by running the tracking system more often than the expression tracker to save compute and still have it look fast.
- Blinks were hard to detect using the OpenCV legacy system since it just didn't have enough blendshapes to detect it. This was fixed later on when I switched to MediaPipe.
- MediaPipe, which was the faster and more comprehensive model, crashed on my Pi 4 since it didn't have the necessary instruction sets for it. I ended up fixing this later on by switching to a Pi 5.
- The expression detection was often wrong, for example, giving happy faces when I was making a neutral expression. I ended up fixing this by calibrating the system with values from my own face, which I got by making funny faces at the camera for a few minutes.

<p>$\color{cyan}\text{\bf September 14th}$</p>

In the evening, I decided to switch to a Pi 5 since I wasn't happy with how the expressions looked on the Pi 4. The swap, including reflash and rewire, took approximately 2  hours. The hamster filter was rewritten on MediaPipe with 478 face points and 52 expression scores! :D This meant that blinking, head turning, looking down, and a few other moods were possible. This made my expressions more accurate and faster since it was a Pi 5.

I also added a timelapse mode to the camera. I saw something online about using a timelapse to keep yourself accountable while studying, so I added a 30-minute timelapse system that automatically uploaded the video to the saved photo drive, which also incentivized me to take small breaks every 30 minutes (and fix the posture).

https://github.com/user-attachments/assets/27eb6a7e-6993-401e-8eb0-af38e977b3c4

_Problems and how I fixed them at this stage:_ 
- The first thresholds I'd had were actually measured at the wrong image size, so I re-measured everything at the size that the filter used. (More looking stupid making random faces at a webcam)
- My mouth opening wasn't triggering the mood for a mouth being open. I found that it flipped 38 times in 30 seconds, far too fast to actually be usable. I fixed this by adding a short cooldown so that expressions matched up with what was going on in the camera feed.
- I also found that my system tended to use about the same 7 hamster faces when I had about 25 in the pool. I ended up fixing this with a random system that incentivized my system to pick new stickers at random that matched the expression instead of repeating the same one.

<p>$\color{cyan}\text{\bf September 16th}$</p>

On this day, I decided that I'd actually take what I'd built to my school so that I could take silly photos with my friends. I connected the Pi to my phone's hotspot so that it could upload and sync to Spotify from anywhere. Now I have a bunch of silly photos with my friends!

_Problems and how I fixed them at this stage:_ 
- When I tried to find the videos I'd taken with my friends, I found that my system had a bug that only showed up in offline use, which is that it didn't upload to my Drive if it was offline after the video compiled. I ended up fixing this by adding an auto-upload function that uploaded every file not already synced to my Drive whenever the Pi reconnects to the internet.

<img width="849" height="632" alt="Hamster filter photo with a friend." src="https://github.com/user-attachments/assets/a66712b7-056b-40cb-a245-536684f3ce49" />


<img width="1232" height="925" alt="Using the whiteboard for calendar." src="https://github.com/user-attachments/assets/f7079e9c-4254-4658-b7bd-4cb02776e97e" />


<p>$\color{green}\text{\bf How the Code Changed}$</p>

The main script that I ran on the Pi, which contained the main functionalities and aggregated all the other tool scripts, was nowplaying.py. This script grew from around 1,200 lines on September 14th when it was on the Pi 4, to 1,400 lines when I upgraded to the Pi 5, and then stayed around that range. Another script, hamster.py, which was the expression detector algorithm, grew from around 300 lines to over 600 when I switched from the HAAR/OpenCV system on the Pi 4 to the MediaPipe system on the Pi 5. The actual files are dated and are in the now-playing history file.

<p>$\color{green}\text{\bf Assistive Tools}$</p>

I did use Claude's Opus 5 model while creating this project for debugging issues and catching errors.
