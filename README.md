# Co-op Matrix Calendar Generator
Generates iCal files for Southern Co-op timetable matricies.

As a collegue for the co-op my shifts may change slightly every week and because of this they send weekly emails of mine (and my co-worker's) timetables. Unfortunately, having to manually enter this into my calendar app every week gets tiring. So, I made this short script for myself. 

A quote from one of my Duty Managers:
> *Thank you! I am forever adding thing to my calendar, this makes it so much nicer!*

## Caveats
- Have to create a Google API project and authorise it to read your emails.
- Has to be run every day at least.
- Has to have the iCal files discoverable on the internet so you can have your calendar app automatically update them.

### Solutions
- Set up email forwarding to your server which the script will read.
- Create a Google add-on (costs money to run though).
- If used infrequently you could have it run on a CF worker which would run only when Google or the respective calendar service asks for a iCal file. But this comes with it's own drawbacks too.


Hopefully you find this script useful like me.