# Demo-Experiment for Tobii pro eyetracker using psychopy
An Experiment by using Tobii pro Controller 


The eye tracking experiment on PsychoPy 3 is compatible with the Tobii pro eye-tracker

Requirements:
- version of the PsychoPy3 2020.2.4
- the installed Tobii pro SDK
-Tobii pro controller https://github.com/janfreyberg/tobii-psychopy/tree/master/tobii-psychopy

The code provides the outlook on the eye-tracking experiment with the given sequence:
- 0.5 s. blanck screen with trigger 1001
- 0.5 s. fixation cross with trigger 2001
- decision with trigger 3001

In case we want to see the direction of the gaze, uncomment "draw_gaze_dot" in each of the above mentioned sequences (namely instructions_blank_screen, instructions_fixation_cross, instructions_choice_decision)

The experiment saves the decision output for n trials (here the number of trials is 2 for the testing purposes), as well as the eye gaze data.

The decision data is organized in the columns as follows:
['Subject_id','Condition', 'Decision', 'Trigger','Item number', 'c1','c2','c3','c4','c5','c6','m1','m2','m3','m4','m5','m6', 'Reaction time', 'Reaction time since decision screen start'],
where 'c1','c2','c3','c4','c5','c6','m1','m2','m3','m4','m5','m6' are the values of the proposed choice in the table for the left and right side respectively.

The decision data is saved in .csv in the format of  "subject_id+'_decision_output'+localtime", and eye-tracking data is saved as "subject_id+eyetracking_output+localtime".

# Licence
GPLv3 (https://github.com/hsogo/psychopy_tobii_controller/blob/master/LICENCE)

# Citation
Please consider to cite PsychoPy to encourage open-source projects:

(APA formatted)

Peirce, J. (2009). Generating stimuli for neuroscience using PsychoPy. Frontiers in Neuroinformatics, 2, 10. doi:10.3389/neuro.11.010.2008
