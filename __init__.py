from datetime import datetime
import os

import numpy as np
import math as math
import tobii_research as tr
from PIL import Image, ImageDraw
from psychopy import core, event, visual
from psychopy.tools.monitorunittools import (cm2pix, deg2cm, deg2pix, pix2cm,
                                             pix2deg)


__version__ = "0.6.1"



class tobii_controller:
    calib_auto_status= []
    """Tobii controller for PsychoPy.

        tobii_research are required for this module.

    Args:
        win: psychopy.visual.Window object.
        id: the id of eyetracker. Default is 0 (use the first found eye-tracker).
        filename: the name of the data file.

    Attributes:
        shrink_speed: the shrinking speed of target in calibration.
            Default is 1.5.
        calibration_dot_size: the size of the central dot in the
            calibration target. Default is _default_calibration_dot_size
            according to the units of self.win.
        calibration_dot_color: the color of the central dot in the
            calibration target. Default is grey.
        calibration_disc_size: the size of the disc in the
            calibration target. Default is _default_calibration_disc_size
            according to the units of self.win.
        calibration_disc_color: the color of the disc in the
            calibration target. Default is deep blue.
        calibration_target_min: the minimum size of the calibration target.
            Default is 0.2.
        numkey_dict: keys used for calibration. Default is the number pad.
            If it is changed, the keys in calibration results will not
            update accordingly (my bad), be cautious!
        update_calibration: the presentation of calibration target.
            Default is auto calibration.
    """
    
    _default_numkey_dict = {
        "0": -1,
        "num_0": -1,
        "1": 0,
        "num_1": 0,
        "2": 1,
        "num_2": 1,
        "3": 2,
        "num_3": 2,
        "4": 3,
        "num_4": 3,
        "5": 4,
        "num_5": 4,
        "6": 5,
        "num_6": 5,
        "7": 6,
        "num_7": 6,
        "8": 7,
        "num_8": 7,
        "9": 8,
        "num_9": 8,
    }
    _default_calibration_dot_size = {
        "norm": 0.02,
        "height": 0.01,
        "pix": 10.0,
        "degFlatPos": 0.25,
        "deg": 0.25,
        "degFlat": 0.25,
        "cm": 0.25,
    }
    _default_calibration_disc_size = {
        "norm": 0.08,
        "height": 0.04,
        "pix": 40.0,
        "degFlatPos": 1.0,
        "deg": 1.0,
        "degFlat": 1.0,
        "cm": 1.0,
    }
    _shrink_speed = 1.5
    _shrink_sec = 3 / _shrink_speed
    calibration_dot_color = (0, 0, 0)
    calibration_disc_color = (-1, -1, 0)
    calibration_target_min = 0.2
    update_calibration = None
    

    def __init__(self, win, id=0, filename="gaze_TOBII_output.tsv"):
        self.eyetracker_id = id
        self.win = win
        self.filename = filename
        self.numkey_dict = self._default_numkey_dict
        self.calibration_dot_size = self._default_calibration_dot_size[
            self.win.units]
        self.calibration_disc_size = self._default_calibration_disc_size[
            self.win.units]

        eyetrackers = tr.find_all_eyetrackers()

        if len(eyetrackers) == 0:
            raise RuntimeError("No Tobii eyetrackers")

        try:
            self.eyetracker = eyetrackers[self.eyetracker_id]
        except:
            raise ValueError(
                "Invalid eyetracker ID {}\n({} eyetrackers found)".format(
                    self.eyetracker_id, len(eyetrackers)))

        self.calibration = tr.ScreenBasedCalibration(self.eyetracker)
        self.update_calibration = self._update_calibration_auto
        self.gaze_data = []

    def _on_gaze_data(self, gaze_data):
        """Callback function used by Tobii SDK.

        Args:
            gaze_data: gaze data provided by the eye tracker.

        Returns:
            None
        """
        self.gaze_data.append(gaze_data)

    def _get_psychopy_pos(self, p, units=None):
        """Convert Tobii ADCS coordinates to PsychoPy coordinates.

        Args:
            p: Gaze position (x, y) in Tobii ADCS.
            units: The PsychoPy coordinate system to use.

        Returns:
            Gaze position in PsychoPy coordinate systems. For example: (0,0).
        """
        if units is None:
            units = self.win.units

        if units == "norm":
            return (2 * p[0] - 1, -2 * p[1] + 1)
        elif units == "height":
            return ((p[0] - 0.5) * (self.win.size[0] / self.win.size[1]),
                    -p[1] + 0.5)
        elif units in ["pix", "cm", "deg", "degFlat", "degFlatPos"]:
            p_pix = self._tobii2pix(p)
            if units == "pix":
                return p_pix
            elif units == "cm":
                return tuple(pix2cm(pos, self.win.monitor) for pos in p_pix)
            elif units == "deg":
                tuple(pix2deg(pos, self.win.monitor) for pos in p_pix)
            else:
                return tuple(
                    pix2deg(np.array(p_pix),
                            self.win.monitor,
                            correctFlat=True))
        else:
            raise ValueError("unit ({}) is not supported.".format(units))

    def _get_tobii_pos(self, p, units=None):
        """Convert PsychoPy coordinates to Tobii ADCS coordinates.

        Args:
            p: Gaze position (x, y) in PsychoPy coordinate systems.
            units: The PsychoPy coordinate system of p.

        Returns:
            Gaze position in Tobii ADCS. For example: (0,0).
        """
        if units is None:
            units = self.win.units

        if units == "norm":
            return (p[0] / 2 + 0.5, p[1] / -2 + 0.5)
        elif units == "height":
            return (p[0] * (self.win.size[1] / self.win.size[0]) + 0.5,
                    -p[1] + 0.5)
        elif units == "pix":
            return self._pix2tobii(p)
        elif units in ["cm", "deg", "degFlat", "degFlatPos"]:
            if units == "cm":
                p_pix = (cm2pix(p[0], self.win.monitor),
                         cm2pix(p[1], self.win.monitor))
            elif units == "deg":
                p_pix = (
                    deg2pix(p[0], self.win.monitor),
                    deg2pix(p[1], self.win.monitor),
                )
            elif units in ["degFlat", "degFlatPos"]:
                p_pix = deg2pix(np.array(p),
                                self.win.monitor,
                                correctFlat=True)
            p_pix = tuple(round(pos) for pos in p_pix)
            return self._pix2tobii(p_pix)
        else:
            raise ValueError("unit ({}) is not supported".format(units))

    def _pix2tobii(self, p):
        """Convert PsychoPy pixel coordinates to Tobii ADCS.

            Called by _get_tobii_pos.

        Args:
            p: Gaze position (x, y) in pixels.

        Returns:
            Gaze position in Tobii ADCS. For example: (0,0).
        """
        return (p[0] / self.win.size[0] + 0.5, -p[1] / self.win.size[1] + 0.5)

    def _tobii2pix(self, p):
        """Convert Tobii ADCS to PsychoPy pixel coordinates.

            Called by _get_psychopy_pos.

        Args:
            p: Gaze position (x, y) in Tobii ADCS.

        Returns:
            Gaze position in PsychoPy pixels coordinate system. For example: (0,0).
        """
        return (round(self.win.size[0] * (p[0] - 0.5)),
                round(-self.win.size[1] * (p[1] - 0.5)))

    def _get_psychopy_pos_from_trackbox(self, p, units=None):
        """Convert Tobii TBCS coordinates to PsychoPy coordinates.

            Called by show_status.

        Args:
            p: Gaze position (x, y) in Tobii TBCS.
            units: The PsychoPy coordinate system to use.

        Returns:
            Gaze position in PsychoPy coordinate systems. For example: (0,0).
        """
        if units is None:
            units = self.win.units

        if units == "norm":
            return (-2 * p[0] + 1, -2 * p[1] + 1)
        elif units == "height":
            return ((-p[0] + 0.5) * (self.win.size[0] / self.win.size[1]),
                    -p[1] + 0.5)
        elif units in ["pix", "cm", "deg", "degFlat", "degFlatPos"]:
            p_pix = (
                round((-p[0] + 0.5) * self.win.size[0]),
                round((-p[1] + 0.5) * self.win.size[1]),
            )
            if units == "pix":
                return p_pix
            elif units == "cm":
                return tuple(pix2cm(pos, self.win.monitor) for pos in p_pix)
            elif units == "deg":
                return tuple(pix2deg(pos, self.win.monitor) for pos in p_pix)
            else:
                return tuple(
                    pix2deg(np.array(p_pix),
                            self.win.monitor,
                            correctFlat=True))
        else:
            raise ValueError("unit ({}) is not supported.".format(units))

    def _flush_to_file(self):
        """Write data to disk.

        Args:
            None

        Returns:
            None
        """
        self.datafile.flush()  # internal buffer to RAM
        os.fsync(self.datafile.fileno())  # RAM file cache to disk

    def _write_record(self, record):
        """Write the Tobii output to the data file.

        Args:
            record: reformed gaze data

        Returns:
            None
        """
        self.datafile.write(
            "{0}\t{1}\t{2}\t{3}\t{4}\t{5}\t{6}\t{7}\t{8}\t{9}\t{10}\t{11}\t{12}\t{13}"
            .format(*record))

    def _convert_tobii_record(self, record):
        """Convert tobii coordinates to output style.

        Args:
            record: raw gaze data

        Returns:
            reformed gaze data
        """
        lp = self._get_psychopy_pos(record["left_gaze_point_on_display_area"])
        rp = self._get_psychopy_pos(record["right_gaze_point_on_display_area"])

        # gaze
        if not (record["left_gaze_point_validity"]
                or record["right_gaze_point_validity"]):  # not detected
            ave = (np.nan, np.nan)
        elif not record["left_gaze_point_validity"]:
            ave = rp  # use right eye
        elif not record["right_gaze_point_validity"]:
            ave = lp  # use left eye
        else:
            ave = ((lp[0] + rp[0]) / 2.0, (lp[1] + rp[1]) / 2.0)

        # pupil
        if not (record["left_pupil_validity"]
                or record["right_pupil_validity"]):  # not detected
            pup = np.nan
        elif not record["left_pupil_validity"]:
            pup = record["right_pupil_diameter"]  # use right pupil
        elif not record["right_pupil_validity"]:
            pup = record["left_pupil_diameter"]  # use left pupil
        else:
            pup = (record["left_pupil_diameter"] +
                   record["right_pupil_diameter"]) / 2.0

        return [
            round((record["system_time_stamp"] - self.t0) / 1000.0, 1),
            round(lp[0], 4),
            round(lp[1], 4),
            int(record["left_gaze_point_validity"]),
            round(rp[0], 4),
            round(rp[1], 4),
            int(record["right_gaze_point_validity"]),
            round(ave[0], 4),
            round(ave[1], 4),
            round(record["left_pupil_diameter"], 4),
            int(record["left_pupil_validity"]),
            round(record["right_pupil_diameter"], 4),
            int(record["right_pupil_validity"]),
            round(pup, 4)] # yapf: disable

    def _flush_data(self):
        """Wrapper for writing the header and data to the data file.

        Args:
            None

        Returns:
            None
        """
        if not self.gaze_data:
            # do nothing when there's no data
            print("No data were collected. Do nothing now...")
            return

        if self.recording:
            # do nothing while recording
            print("Still recording. Do nothing now...")
            return

        #self.datafile.write("Session Start\n")
        # write header
        self.datafile.write("\t".join([
            "TimeStamp",
            "GazePointXLeft",
            "GazePointYLeft",
            "ValidityLeft",
            "GazePointXRight",
            "GazePointYRight",
            "ValidityRight",
            "GazePointX",
            "GazePointY",
            "PupilSizeLeft",
            "PupilValidityLeft",
            "PupilSizeRight",
            "PupilValidityRight",
            "PupilSize"]) + "\n") # yapf: disable
        self._flush_to_file()

        for gaze_data in self.gaze_data:
            output = self._convert_tobii_record(gaze_data)
            self._write_record(output)
            self.datafile.write("\n")
        else:
            # write the events in the end of data
            for event in self.event_data:
                self.datafile.write("{0}\t{1}\n".format(*event))
        #self.datafile.write("Session End\n")
        self._flush_to_file()

    def _collect_calibration_data(self, p):
        """Callback function used by Tobii calibration in run_calibration.

        Args:
            p: the calibration point

        Returns:
            None
        """
        self.calibration.collect_data(*self._get_tobii_pos(p))

    def _open_datafile(self):
        """Open a file for gaze data.

        Args:
            None

        Returns:
            None
        """
        self.datafile = open(self.filename, "w")
        #self.datafile.write("Recording date:\t{}\n".format(
        #    datetime.now().strftime("%Y/%m/%d")))
        #self.datafile.write("Recording time:\t{}\n".format(
        #    datetime.now().strftime("%H:%M:%S")))
        #self.datafile.write(
        #    "Recording resolution:\t{} x {}\n".format(*self.win.size))
        #self.datafile.write("PsychoPy units:\t{}\n".format(self.win.units))
        #self._flush_to_file()

    def start_recording(self, filename=None, newfile=True):
        """Start recording

        Args:
            filename: the name of the data file. If None, use default name.
                Default is None.
            newfile: open a new file to save data. Default is True.

        Returns:
            None
        """
        if filename is not None:
            self.filename = filename

        if newfile:
            self._open_datafile()

        self.gaze_data = []
        self.event_data = []
        self.eyetracker.subscribe_to(tr.EYETRACKER_GAZE_DATA,
                                     self._on_gaze_data,
                                     as_dictionary=True)
        core.wait(0.5)  # wait a bit for the eye tracker to get ready
        self.recording = True
        self.t0 = tr.get_system_time_stamp()

    def stop_recording(self):
        """Stop recording.

        Args:
            None

        Returns:
            None
        """
        if self.recording:
            self.eyetracker.unsubscribe_from(tr.EYETRACKER_GAZE_DATA,
                                             self._on_gaze_data)
            self.recording = False
            # time correction for event datas
            self.event_data = [(round((x[0] - self.t0) / 1000.0, 1), x[1])
                               for x in self.event_data]
            self._flush_data()
        else:
            print("A recording has not been started. Do nothing now...")

    def get_current_gaze_position(self):
        """Get the newest gaze position.

        Args:
            None

        Returns:
            A tuple of the newest gaze position in PsychoPy coordinate system.
            For example: (0, 0).
        """
        if not self.gaze_data:
            return (np.nan, np.nan)
        else:
            gaze_data = self.gaze_data[-1]
            lp = self._get_psychopy_pos(
                gaze_data["left_gaze_point_on_display_area"])
            rp = self._get_psychopy_pos(
                gaze_data["right_gaze_point_on_display_area"])
            if not (gaze_data["left_gaze_point_validity"]
                    or gaze_data["right_gaze_point_validity"]):  # not detected
                return (np.nan, np.nan)
            elif not gaze_data["left_gaze_point_validity"]:
                ave = rp  # use right eye
            elif not gaze_data["right_gaze_point_validity"]:
                ave = lp  # use left eye
            else:
                ave = ((lp[0] + rp[0]) / 2.0, (lp[1] + rp[1]) / 2.0)

            return tuple(round(pos, 4) for pos in ave)

    def get_current_pupil_size(self):
        """Get the newest pupil size.

        Args:
            None

        Returns:
            A tuple of the newest pupil diameter reported by the eye-tracker.
            For example: (4, 4).
        """
        if not self.gaze_data:
            return np.nan
        else:
            gaze_data = self.gaze_data[-1]
            if not (gaze_data["left_pupil_validity"]
                    or gaze_data["right_pupil_validity"]):  # not detected
                pup = np.nan
            elif not gaze_data["left_pupil_validity"]:
                pup = gaze_data["right_pupil_diameter"]  # use right pupil
            elif not gaze_data["right_pupil_validity"]:
                pup = gaze_data["left_pupil_diameter"]  # use left pupil
            else:
                pup = ((gaze_data["left_pupil_diameter"] +
                        gaze_data["right_pupil_diameter"]) / 2.0)

            return round(pup, 4)

    def record_event(self, event):
        """Record events with timestamp.

            This method works only during recording.

        Args:
            event: the event

        Returns:
            None
        """
        if not self.recording:
            return

        self.event_data.append([tr.get_system_time_stamp(), event])

    def close(self):
        """Close the data file.

        Args:
            None

        Returns:
            None
        """
        self.datafile.close()

    def run_calibration(self, calibration_points, decision_key="space"):
        """Run calibration

        Args:
            calibration_points: list of position of the calibration points.
            decision_key: the key to leave the procedure. Default is space.

        Returns:
            bool: The status of calibration. True for success, False otherwise.
        """
        if self.eyetracker is None:
            raise RuntimeError("Eyetracker is not found.")

        if not (2 <= len(calibration_points) <= 9):
            raise ValueError("Calibration points must be 2~9")

        else:
            self.numkey_dict = {
                k: v
                for k, v in self.numkey_dict.items()
                if v < len(calibration_points)
            }
        # prepare calibration stimuli
        self.calibration_target_dot = visual.Circle(
            self.win,
            radius=self.calibration_dot_size,
            fillColor=self.calibration_dot_color,
            lineColor=self.calibration_dot_color,
        )
        self.calibration_target_disc = visual.Circle(
            self.win,
            radius=self.calibration_disc_size,
            fillColor=self.calibration_disc_color,
            lineColor=self.calibration_disc_color,
        )
        self.retry_marker = visual.Circle(
            self.win,
            radius=self.calibration_dot_size,
            fillColor=self.calibration_dot_color,
            lineColor=self.calibration_disc_color,
            autoLog=False,
        )
        if self.win.units == "norm":  # fix oval
            self.calibration_target_dot.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
            self.calibration_target_disc.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
            self.retry_marker.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
        result_msg = visual.TextStim(
            self.win,
            pos=(0, -self.win.size[1] / 4),
            color="white",
            units="pix",
            autoLog=False,
        )

        self.calibration.enter_calibration_mode()

        self.original_calibration_points = calibration_points[:]
        # set all points
        cp_num = len(self.original_calibration_points)
        self.retry_points = list(range(cp_num))

        in_calibration_loop = True
        event.clearEvents()
        while in_calibration_loop:
            self.calibration_points = [
                self.original_calibration_points[x] for x in self.retry_points
            ]

            # clear the display
            self.win.flip()
            self.update_calibration()
            self.calibration_result = self.calibration.compute_and_apply()
            self.win.flip()

            result_img = self._show_calibration_result()
            result_msg.setText(
                #"Accept/Retry: {k}\n"
                #"Select/Deselect all points: 0\n"
                "if the lines are not in the circle recalibration is needed\n"
                "Continue: Space".format(k=decision_key, p=cp_num))

            waitkey = True
            self.retry_points = []
            while waitkey:
                for key in event.getKeys():
                    if key in [decision_key, "escape"]:
                        waitkey = False
                    elif key in self.numkey_dict:
                        if self.numkey_dict[key] == -1:
                            if len(self.retry_points) == cp_num:
                                self.retry_points = []
                            else:
                                self.retry_points = list(range(cp_num))
                        else:
                            key_index = self.numkey_dict[key]
                            if key_index < cp_num:
                                if key_index in self.retry_points:
                                    self.retry_points.remove(key_index)
                                else:
                                    self.retry_points.append(key_index)

                result_img.draw()
                if len(self.retry_points) > 0:
                    for retry_p in self.retry_points:
                        self.retry_marker.setPos(
                            self.original_calibration_points[retry_p])
                        self.retry_marker.draw()

                result_msg.draw()
                self.win.flip()

            if key == decision_key:
                if len(self.retry_points) == 0:
                    retval = True
                    in_calibration_loop = False
                else:  # retry
                    for point_index in self.retry_points:
                        x, y = self._get_tobii_pos(
                            self.original_calibration_points[point_index])
                        self.calibration.discard_data(x, y)
            elif key == "escape":
                retval = False
                in_calibration_loop = False

        self.calibration.leave_calibration_mode()

        return retval

    def _show_calibration_result(self):
        global calib_auto_status
        img = Image.new("RGBA", tuple(self.win.size))
        img_draw = ImageDraw.Draw(img)
        img_draw1 = ImageDraw.Draw(img)
        result_img = visual.SimpleImageStim(self.win, img, autoLog=False)
        img_draw.rectangle(((0, 0), tuple(self.win.size)), fill=(0, 0, 0, 0))
        r='0'
        l='0'
        calib_auto_status_l =[]
        self.calib_auto_status= calib_auto_status_l
        if self.calibration_result.status == tr.CALIBRATION_STATUS_FAILURE:
            # computeCalibration failed.
            pass
        else:
            if len(self.calibration_result.calibration_points) == 0:
                pass
            else:
                for calibration_point in self.calibration_result.calibration_points:
                    p = calibration_point.position_on_display_area
                    for calibration_sample in calibration_point.calibration_samples:
                        lp = calibration_sample.left_eye.position_on_display_area
                        rp = calibration_sample.right_eye.position_on_display_area
                        distancel = math.sqrt( ((p[0]-lp[0])**2)+((p[1]-lp[1])**2) ) 
                        distancer = math.sqrt( ((p[0]-lp[0])**2)+((p[1]-lp[1])**2) ) 
                        if distancel <= 1.36:
                            if distancer <= 1.36:
                                calib_auto_status_l.append('1')
                                r= '1'
                                print('dl:',distancel)
                                print('dr:',distancer)
                                print('r:', r)

                                print('p:',p[0])
                                print('lp:',lp[0])
                                print('rp:',rp[0])
                                print('status:' ,calib_auto_status_l)
                        else:
                            calib_auto_status_l.append('0')
                            r= '0'
                            print('r:', r)
                            print('status:' ,calib_auto_status_l)
                            #elif distancel > 0.04:
                            #    r='0'
                            #3    l='0'
                            #    print('r:', r)
                            #    print('l:', l)
                            #   print('dl:',distancel)
                            #    print('dr:',distancer)
                            #    print('r:', r)
                            #    print('p:',p[0])
                            #    print('lp:',lp[0])
                            #    print('rp:',rp[0])
                                
                        if (calibration_sample.left_eye.validity ==
                                tr.VALIDITY_VALID_AND_USED):
                            img_draw.line(
                                (
                                    (p[0] * self.win.size[0],
                                     p[1] * self.win.size[1]),
                                    (
                                        lp[0] * self.win.size[0],
                                        lp[1] * self.win.size[1],
                                    ),
                                ),
                                fill=(0, 255, 0, 255),
                            )
                        if (calibration_sample.right_eye.validity ==
                                tr.VALIDITY_VALID_AND_USED):
                            img_draw.line(
                                (
                                    (p[0] * self.win.size[0],
                                     p[1] * self.win.size[1]),
                                    (
                                        rp[0] * self.win.size[0],
                                        rp[1] * self.win.size[1],
                                    ),
                                ),
                                fill=(255, 0, 0, 255),
                            )
                    img_draw.ellipse(
                        (
                            (p[0] * self.win.size[0] - 3,
                             p[1] * self.win.size[1] - 3),
                            (p[0] * self.win.size[0] + 3,
                             p[1] * self.win.size[1] + 3),
                        ),
                        outline=(0, 0, 0, 255),
                    )
                    #changing size of the accuracy circle
                    #cir = visual.Circle(self.win,radius=1.136,lineColor="white")
                    #psychopy.visual.Polygon(win, edges=3, radius=0.5, **kwargs)
                    
                    img_draw1.ellipse(
                        (
                            (p[0] * self.win.size[0] - 76.8,
                             p[1] * self.win.size[1] - 76.8),
                            (p[0] * self.win.size[0] + 76.8,
                             p[1] * self.win.size[1] + 76.8),
                        ),
                        outline=(255, 255, 255, 255),
                    )
                    
        #cir.draw()
        result_img.setImage(img)
        return result_img

    def _update_calibration_auto(self):
        """Automatic calibration procedure."""
        # start calibration
        event.clearEvents()
        clock = core.Clock()
        for current_point_index in self.retry_points:
            self.calibration_target_disc.setPos(
                self.original_calibration_points[current_point_index])
            self.calibration_target_dot.setPos(
                self.original_calibration_points[current_point_index])
            clock.reset()
            while True:
                t = clock.getTime() * self.shrink_speed
                self.calibration_target_disc.setRadius([
                    (np.sin(t)**2 + self.calibration_target_min) *
                    self.calibration_disc_size
                ])
                self.calibration_target_dot.setRadius([
                    (np.sin(t)**2 + self.calibration_target_min) *
                    self.calibration_dot_size
                ])
                self.calibration_target_disc.draw()
                self.calibration_target_dot.draw()
                if clock.getTime() >= self._shrink_sec:
                    core.wait(0.5)
                    self._collect_calibration_data(
                        self.original_calibration_points[current_point_index])
                    break

                self.win.flip()

    def show_status(self):
        """Showing the participant's gaze position in track box.

        Args:
            None

        Returns:
            None
        """
        bgrect = visual.Rect(
            self.win,
            pos=(0, 0.4),
            width=0.25,
            height=0.2,
            lineColor="white",
            fillColor="black",
            units="height",
            autoLog=False,
        )

        leye = visual.Circle(
            self.win,
            size=0.02,
            units="height",
            lineColor=None,
            fillColor="green",
            autoLog=False,
        )

        reye = visual.Circle(
            self.win,
            size=0.02,
            units="height",
            lineColor=None,
            fillColor="red",
            autoLog=False,
        )

        zbar = visual.Rect(
            self.win,
            pos=(0, 0.28),
            width=0.25,
            height=0.03,
            lineColor="green",
            fillColor="green",
            units="height",
            autoLog=False,
        )

        zc = visual.Rect(
            self.win,
            pos=(0, 0.28),
            width=0.01,
            height=0.03,
            lineColor="white",
            fillColor="white",
            units="height",
            autoLog=False,
        )

        zpos = visual.Rect(
            self.win,
            pos=(0, 0.28),
            width=0.005,
            height=0.03,
            lineColor="black",
            fillColor="black",
            units="height",
            autoLog=False,
        )
        inst = visual.TextStim(self.win, text="Add the instruction for callibration here!", height=20, alignText='left', units='pix', pos = [0,0],color=[255,255,255],colorSpace='rgb255')
        inst.size = 6
        if self.eyetracker is None:
            raise RuntimeError("Eyetracker is not found.")

        self.eyetracker.subscribe_to(tr.EYETRACKER_USER_POSITION_GUIDE,
                                     self._on_gaze_data,
                                     as_dictionary=True)
        core.wait(0.5)  # wait a bit for the eye tracker to get ready

        b_show_status = True

        while b_show_status:
            inst.draw()
            bgrect.draw()
            zbar.draw()
            zc.draw()
            gaze_data = self.gaze_data[-1]
            lv = gaze_data["left_user_position_validity"]
            rv = gaze_data["right_user_position_validity"]
            lx, ly, lz = gaze_data["left_user_position"]
            rx, ry, rz = gaze_data["right_user_position"]
            if lv:
                lx, ly = self._get_psychopy_pos_from_trackbox([lx, ly],
                                                              units="height")
                leye.setPos((round(lx * 0.25, 4), round(ly * 0.2 + 0.4, 4)))
                leye.draw()
            if rv:
                rx, ry = self._get_psychopy_pos_from_trackbox([rx, ry],
                                                              units="height")
                reye.setPos((round(rx * 0.25, 4), round(ry * 0.2 + 0.4, 4)))
                reye.draw()
            if lv or rv:
                zpos.setPos((
                    round((((lz * int(lv) + rz * int(rv)) /
                            (int(lv) + int(rv))) - 0.5) * 0.125, 4),
                    0.28,
                ))
                zpos.draw()

            for key in event.getKeys():
                if key == "space":
                    b_show_status = False
                    break

            self.win.flip()

        self.eyetracker.unsubscribe_from(tr.EYETRACKER_USER_POSITION_GUIDE,
                                         self._on_gaze_data)


    # property getters and setters for parameter changes
    @property
    def shrink_speed(self):
        return self._shrink_speed

    @shrink_speed.setter
    def shrink_speed(self, value):
        self._shrink_speed = value
        # adjust the duration of shrinking
        self._shrink_sec = 3 / self._shrink_speed

    @property
    def shrink_sec(self):
        return self._shrink_sec

    @shrink_sec.setter
    def shrink_sec(self, value):
        self._shrink_sec = value


class infant_tobii_controller(tobii_controller):
    """Tobii controller for PsychoPy with children-friendly calibration procedure.

        This is a subclass of tobii_controller, with some modification for developmental research.

    Args:
        win: psychopy.visual.Window object.
        id: the id of eyetracker.
        filename: the name of the data file.

    Attributes:
        shrink_speed: the shrinking speed of target in calibration.
            Default is 1.
        numkey_dict: keys used for calibration. Default is the number pad.
    """
    def __init__(self, win, id=0, filename="gaze_TOBII_output.tsv"):
        super().__init__(win, id, filename)
        self.update_calibration = self._update_calibration_infant
        # slower for infants
        self.shrink_speed = 1

    def _update_calibration_infant(self,
                                   collect_key="space",
                                   exit_key="return"):
        """The calibration procedure designed for infants.

            An implementation of run_calibration() in psychopy_tobii_controller.

        Args:
            collect_key: the key to start collecting samples. Default is space.
            exit_key: the key to finish and leave the current calibration
                procedure. It should not be confused with `decision_key`, which
                is used to leave the whole calibration process. `exit_key` is
                used to leave the current calibration, the user may recalibrate
                or accept the results afterwards. Default is return (Enter)

        Returns:
            None
        """
        # start calibration
        event.clearEvents()
        current_point_index = -1
        in_calibration = True
        clock = core.Clock()
        while in_calibration:
            # get keys
            keys = event.getKeys()
            for key in keys:
                if key in self.numkey_dict:
                    current_point_index = self.numkey_dict[key]
                    # play the sound if it exists
                    if self._audio is not None:
                        if current_point_index in self.retry_points:
                            self._audio.play()
                elif key == collect_key:
                    # allow the participant to focus
                    core.wait(0.5)
                    # collect samples when space is pressed
                    if current_point_index in self.retry_points:
                        self._collect_calibration_data(
                            self.
                            original_calibration_points[current_point_index])
                        current_point_index = -1
                        # stop the sound
                        if self._audio is not None:
                            self._audio.stop()
                elif key == exit_key:
                    # exit calibration when return is presssed
                    in_calibration = False
                    break

            # draw calibration target
            if current_point_index in self.retry_points:
                self.targets[current_point_index].setPos(
                    self.original_calibration_points[current_point_index])
                t = clock.getTime() * self.shrink_speed
                newsize = [(np.sin(t)**2 + self.calibration_target_min) * e
                           for e in self.target_original_size]
                self.targets[current_point_index].setSize(newsize)
                self.targets[current_point_index].draw()
            self.win.flip()

    def run_calibration(self,
                        calibration_points,
                        infant_stims,
                        audio=None,
                        decision_key="space"):
        """Run calibration

            How to use:
                - Use 1~9 to present calibration stimulus and 0 to hide the target.
                - Press space to start collect calibration samples.
                - Press return (Enter) to finish the calibration and show the result.
                - Choose the points to recalibrate with 1~9.
                - Press decision_key (default is space) to accept the calibration or recalibrate.

            The experimenter should manually show the stimulus and collect data
            when the subject is paying attention to the stimulus.

        Args:
            calibration_points: list of position of the calibration points.
            infant_stims: list of images to attract the infant.
            audio: the psychopy.sound.Sound object to play during calibration.
                If None, no sound will be played. Default is None.
            decision_key: the key to leave the procedure. Default is space.

        Returns:
            bool: The status of calibration. True for success, False otherwise.
        """
        if self.eyetracker is None:
            raise RuntimeError("Eyetracker is not found.")

        if not (2 <= len(calibration_points) <= 9):
            raise ValueError("Calibration points must be 2~9")

        else:
            self.numkey_dict = {
                k: v
                for k, v in self.numkey_dict.items()
                if v < len(calibration_points)
            }

        # prepare calibration stimuli
        try:
            self.targets = [
                visual.ImageStim(self.win, image=v, autoLog=False)
                for v in infant_stims
            ]
        except:
            raise RuntimeError(
                "Unable to load the calibration images.\n"
                "Is the number of images equal to the number of calibration points?"
            )

        self._audio = audio

        self.target_original_size = self.targets[0].size
        self.retry_marker = visual.Circle(
            self.win,
            radius=self.calibration_dot_size,
            fillColor=self.calibration_dot_color,
            lineColor=self.calibration_disc_color,
            autoLog=False,
        )
        if self.win.units == "norm":  # fix oval
            self.retry_marker.setSize(
                [float(self.win.size[1]) / self.win.size[0], 1.0])
        result_msg = visual.TextStim(
            self.win,
            pos=(0, -self.win.size[1] / 4),
            color="white",
            units="pix",
            autoLog=False,
        )

        self.calibration.enter_calibration_mode()

        self.original_calibration_points = calibration_points[:]
        # set all points
        cp_num = len(self.original_calibration_points)
        self.retry_points = list(range(cp_num))

        in_calibration_loop = True
        event.clearEvents()
        while in_calibration_loop:
            # randomization of calibration targets
            np.random.shuffle(self.targets)
            self.calibration_points = [
                self.original_calibration_points[x] for x in self.retry_points
            ]

            # clear the display
            self.win.flip()
            self.update_calibration()
            self.calibration_result = self.calibration.compute_and_apply()
            self.win.flip()

            result_img = self._show_calibration_result()
            result_msg.setText(
                #"Accept/Retry: {k}\n"
                #"Select/Deselect all points: 0\n"
                "if the lines are not in the circle recalibrate is needed\n"
                "Continue: Space".format(k=decision_key, p=cp_num))

            waitkey = True
            self.retry_points = []
            while waitkey:
                for key in event.getKeys():
                    if key in [decision_key, "escape"]:
                        waitkey = False
                    elif key in self.numkey_dict:
                        if self.numkey_dict[key] == -1:
                            if len(self.retry_points) == cp_num:
                                self.retry_points = []
                            else:
                                self.retry_points = list(range(cp_num))
                        else:
                            key_index = self.numkey_dict[key]
                            if key_index < cp_num:
                                if key_index in self.retry_points:
                                    self.retry_points.remove(key_index)
                                else:
                                    self.retry_points.append(key_index)

                result_img.draw()
                if len(self.retry_points) > 0:
                    for retry_p in self.retry_points:
                        self.retry_marker.setPos(
                            self.original_calibration_points[retry_p])
                        self.retry_marker.draw()

                result_msg.draw()
                self.win.flip()

            if key == decision_key:
                if len(self.retry_points) == 0:
                    retval = True
                    in_calibration_loop = False
                else:  # retry
                    for point_index in self.retry_points:
                        x, y = self._get_tobii_pos(
                            self.original_calibration_points[point_index])
                        self.calibration.discard_data(x, y)
            elif key == "escape":
                retval = False
                in_calibration_loop = False

        self.calibration.leave_calibration_mode()

        return retval

    # Collect looking time
    def collect_lt(self, max_time, min_away, blink_dur=1):
        """Collect looking time data in runtime

            Collect and calculate looking time in runtime. Also end the trial
            automatically when the participant look away.

        Args:
            max_time: maximum looking time in seconds.
            min_away: minimum duration to stop in seconds.
            blink_dur: the tolerable duration of missing data in seconds.

        Returns:
            lt (float): The looking time in the trial.
        """
        trial_timer = core.Clock()
        absence_timer = core.Clock()
        away_time = []

        looking = True
        trial_timer.reset()
        absence_timer.reset()

        while trial_timer.getTime() <= max_time:
            gaze_data = self.gaze_data[-1]
            lv = gaze_data["left_gaze_point_validity"]
            rv = gaze_data["right_gaze_point_validity"]

            if any((lv, rv)):
                # if the last sample is missing
                if not looking:
                    away_dur = absence_timer.getTime()
                    # if missing samples are larger than the threshold of termination
                    if away_dur >= min_away:
                        away_time.append(away_dur)
                        lt = trial_timer.getTime() - np.sum(away_time)
                        # stop the trial
                        return round(lt, 3)
                    # if missing samples are larger than blink duration
                    elif away_dur >= blink_dur:
                        away_time.append(away_dur)
                    # if missing samples are tolerable
                    else:
                        pass
                looking = True
                absence_timer.reset()
            else:
                if absence_timer.getTime() >= min_away:
                    away_dur = absence_timer.getTime()
                    away_time.append(away_dur)
                    lt = trial_timer.getTime() - np.sum(away_time)
                    # terminate the trial
                    return round(lt, 3)
                else:
                    pass
                looking = False

            self.win.flip()
        # if the loop is completed, return the looking time
        else:
            lt = max_time - np.sum(away_time)
            return round(lt, 3)
