# mmd_vam_import

This program takes an MMD compatible motion file (*.vmd) and converts it into a
VAM scene file.

# What is MMD?
Miku Miku Dance(MMD)is likely the most popular software out there to create non-professional 3D motions/dances. It's free and very easy to use which is probably why there are a thousands of motion files available on the internet for download. Motion files have a .VMD extension.
You can download it from [here](https://learnmmd.com/http:/learnmmd.com/download-the-latest-version-mikumikudance/)

# Instructions
    One time setup:
        1. Install python (https://realpython.com/installing-python/) if you haven't. This uses Python 3.
        2. Install pip if you don't have it. Should come with Python 3.
        3. Open a command line, run "pip install pyquaternion"
        4. Download vmd.py and base.json

    After setup:
        1. Open vmd.py in any text editor, don't be afraid.
        2. Set the MMD_MOTION_FILE variable to the location of the .vmd file.
        3. Set the VAM_SCENE_BASE variable to the location where the base.json file is saved.
        4. Save the file.
        5. Open a command line. Run python [DIR]\vmd.py, where DIR is where you put the vmd.py file.
        6. The resulting scene file will be VAM_OUT_SCENE.
        5. Tweak! Tweaking the physics of the model is probably the most important part to get decent results.
        See below for how to get better results.

Note: You *have* to use the base scene first. After your motion is done you can change the output scene any way you want.

# For better results:
* The size of the model matters, you should try to match the proportions of the legs, chest, etc.
* The "Hold Rotation" slider dictates how much force should you model put to reach the angle given by MMD. MMD poses sometimes are physically impossible, so you can't always set this slider to max. As a rule of thumb use high hold and low damper for fast dances and quick motion. Use mid damper and low hold for soft motion like pole dances or slow sex.
* MMD relies a *lot* on interpolation and interpolation curves for smoothness. Most vmd files only have a few keyframes and let MMD do most of the work by interpolating in between. While this program can also interpolate (and a little interpolation is ok) the bone paths are not always exactly the same as MMD and can result in weird motions. So, to get around that I "pre-process" .vmd files by registering the position of all the bones on every frame. To do that:
    1. Download http://www.mouserecorder.com/ and open it.
    2. Open MMD and load the motion.
    3. Click Select all under bones.
    4. Press record on Mouse Recorder
    5. Click on Register
    6. Click on > for the next frame.
    7. Stop the recording on Mouse Recorder, clean it up so it only contains the two clicks (Register and >)
    8. Run this at full speed (1000) for the entire length of the motion.
    9. Save the new motion (Edit > Select all bone motion > Save). Use the new file as your motion file.

# Bugs / Known Issues
- Interpolation is WIP needs work. Things like 360 body turns done with a few keyframs only usually result in weirdness.
- Interpolation curves are not currently used. To get around that you can use the mouse recorder method.
- MMD has zero respect for physical body constraints (e.g. lazy MMD authors will rotate an arm by 270deg to save a few keyframes). This looks weird in VAM.
- MMD has no body collision. Legs and arms can go through each other but will cause VAM models to trip and get stuck. Disabling collition is recommended for motions that do that.
- There's a bug that causes the change from the initial basic standing T position to the first dance position to happen too quickly and can create exploding models. Disable collition while working on a scene.

# Credits:
    https://github.com/Darkblader24 for the VMD parsing code.

# How does this work?
This section explains in detail how this code works. If you don't care about the inner workings of it, don't bother reading this section. Also, if you have experience in 3D graphics some of this is gonna be pretty elementary to you. I was completely new to it so I will assume the same of most readers.

A couple of basic concepts first:
  * Motion is a sequence of body poses. And while you may think of a body pose as a set of xyz positions of body parts, you can also express a pose as a set of rotations. E.g. crossing your arms is first rotating your shoulders by ~90 deg towards your chest and then rotating your elbows upwards by 90 deg. In fact, this way of describing poses is much more flexible as the size of the arms doesn't matter (it does in absolute positions). This is how MMD stores pose data per frame except for 3 bones: The "center" and the two feet. Why? I'm not sure, but that's how it works. So it likes rotations for every bone and positions for feet and center.
  * Back to crossing your arms, notice that when you rotate your shoulder towards your chest your elbow also rotates in the same direction and by the same amount, and so does your hand as if they "depended" on the rotation of your shoulder. When you bend your elbow your hand also rotates but not the shoulder.
So there's a "rotation dependency" between bones: The hand's rotation depends on the elbow's rotation and the elbow's rotation in turn depends on the shoulder's rotation.


The first step is to read and extracting the bone name and rotation at each frame of the VMD file. Each chunk of data in the file contains a bone name (in japanese, so it's translated), a frame number, a position XYZ, a rotation XYZW (more on the W later) and interpolation data (not currently used). The extracted data is put in a map for processing.

In order to do the conversion we map the bone names in MMD to the bone names in VMD. The mappings are defined in MMD_TO_VAM_BONE_MAPPINGS. Some bones are perfect matches (LeftShoulder -> lShoulder), but some are approximations (e.g. LowerBody -> pelvis).

Using the bone name mappings, we assign the positions / rotations we got from step (1). But remember, only feet and center use positions, everything else uses rotations. So we turn off position for all bones except those 3. We then put them in the VAM scene file using VAMs animation format which is just some json that looks like this:

    {
      id : [boneName]Animation:
      steps: [{
        timeStep: (the time at which the pose should happen)
        positionOn: True for hip (Center) and l/r foot. False for all others.
        position: x, y z values
        rotationOn: On for all.
        rotation: x, y z, w values (More on the W later)
    }]
    }

Timestep is just the frame number / 30 since MMD is 30 FPS.

That's the whole idea. Pretty simple right? So why wasn't this done a while back?
Well, here's the tricky part: MMD uses relative rotations. VAM uses absolute rotations.

So in the crossing arms example MMD would say you rotated your shoulder 90 deg sideways and then your elbow rotated 90 deg upwards *relative* to the current shoulder rotation. Your hand is rotated 0 relative to your elbow.
But VAM would say you rotated your shoulder by 90deg sideways *and so did your elbow and hand because everything rotates when you turn your shoulder* and your elbow AND hand 90 deg upwards.

So MMD says (x,y,z):

    shoulder:   90,0,0
    elbow:      0,90,0
    hand:       0,0,0

But VAM says (x,y,z):

    shoulder:   90,0,0
    elbow:      90,90,0
    hand:       90,90,0

Notice something? For VAM the rotation of a bone is nothing but the current bone rotation combined (or "added') with the rotation of its "dependencies". That is:

VAM for hand is:

    X: 0(current) + 90 (dependecy)
    Y: 0(current) + 90 (dependecy)
    Z: 0(current) + 0 (dependecy)

VAM for elbow is:

    X: 0(current) + 90 (dependecy)
    Y: 90(current) + 0 (dependecy)
    Z: 0(current) + 0 (dependecy)

In other words, to convert from relative to absolute coordinates you need to combine the current rotation of the bone and the previous bone dependency.

Ok, so recapping. First we extract from the MMD file all the information for each position/rotation for each frame for each bone, translate the names in the process and map them to bones in VAM. Then we iterate over this map and calculate the positions for the chest, then the shoulders (by adding the chest), then the elbows (by adding the shoulders), etc. We store it all and then convert it to VAM's json format. That's it! But, there's a catch.

Turns out "combining" or "adding" rotations in 3 dimensions (aka. Euler angles) by elementary addition doesn't quite work. That is, the combination or sum of two vectors in 3 dimensions (10º,5º,3º) and (2º,5º,3º) is not (12º,10º,6º). In fact the math two combine two rotation vectors in 3 dimensions is pretty ugly, so to combine two rotations you need to use Quaternions.

\- Quat-what???

\- Quaternions.

\- And you multiply to add???

\- Yes, you multiply to add.

 \- In reverse???
 
 \- YES, in reverse. And stop asking that many questions you little bastard. You want to see naked girls dancing right? So read on.

Quaternions are 3 dimensional angles expressed in 4 dimensions. That's where the "W" comes from, for the 4th dimension. I'm pretty sure nobody understands what these things are other than the guy that invented them, and he's already dead. Anyone that says they know what they are is probably lying and should not be trusted. But somehow, the math to combine two rotations when using a 4th dimension is much easier.

Luckily there smarter people than you and I who know more about these things from hell and they've provided a quaternion python package for us mortals, so our interaction with them is minimal. Just know this: if you want to have combine rotation Q1 with rotation Q2 to obtain Q3 then Q3 = Q2 * Q1. That's all you need to know and wanting to know more without a math degree from MIT is foolish.
Also worth noting when they say "multiply" two quaternions it's not really rudimentary multiplication, but an operation involving e, acos, asin, and other ugly things. But for some reason they call it "multiply" and they use the "*" sign so who am I to say different.

Alright, so that's it. Then in pseudocode:

    1. Open and read each chunk of the MMD file.
    2. For each chunk, translate the bone name from JP, extract the frame number, position, rotation
       and interpolation curve (not currently used). Put it all in a map.
    3. Now we need to convert all the coordinates from relative to absolute so:
    4. Iterate over each body part starting with the Center (assigned to hip).
       So for hip just copy the rotations over.
    5. Continue iterating over the dependent body parts next (chest, neck, head, etc).
       On each step combine the rotation using quaternion multiplication. Put it all in another map.
       Do this until the whole body is done.
    6. Iterate again over the new map for each processed frame, converting to the json format.
       We do some tweaks here too (some axises are flipped, the arms are initially rotated in MMD, etc).
    7. Then read in the base scene json, shove in the Animation data and write everything as a new file.

Done!

Well, not really. I came to understand that just as important as having the right rotations, is to have the right physics on the scene. In MMD any motion is possible. A head can be turned a full 180 without any other body part moving. Models are 100% flexible. VAM is way more realistic. Not only do things not turn completely but if you turn the head then the neck, shoulders and chest will also move and not hold their position. In fact, if you try it you'll notice VAM models are not really that flexible and can't hold hard to reach positions very well. They're also pretty slow with fast movements if the motion is dampened.

So the base scene is tweaked to imitate the weird physics of MMD to make models reach positions faster and hold positions much better. It also deals with the knees issue which is that in MMD knees are basically useless as they offer no resistance and bend effortlessly. Still, a lot of tweaking is required to make the motions look more natural as described above.

Alright, that's it. Hopefully now you can help maintain this now :)
