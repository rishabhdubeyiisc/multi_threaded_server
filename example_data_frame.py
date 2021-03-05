"""
# IEEE Std C37.118.2 - 2011 Frame Implementation #

This script provides implementation  of IEEE Standard for Synchrophasor
Data Transfer for Power Systems.

**IEEE C37.118.2 standard** defines four types of frames:

* Data Frames.
* Configuration Frames (multiple versions).
* Command Frames.
* Header Frames.

"""

import collections
from abc import ABCMeta, abstractmethod
from struct import pack, unpack
from time import time
from math import sqrt, atan2

from synchrophasor.utils import crc16xmodem
from synchrophasor.utils import list2bytes


__author__ = "Stevan Sandi"
__copyright__ = "Copyright (c) 2016, Tomo Popovic, Stevan Sandi, Bozo Krstajic"
__credits__ = []
__license__ = "BSD-3"
__version__ = "1.0.0-alpha"


class CommonFrame(metaclass=ABCMeta):
    """
    ## CommonFrame ##

    CommonFrame is abstract class which represents words (fields) common to all frame types.

    Class contains two abstract methods:

    * ``convert2bytes()`` - for converting frame to bytes convenient for sending.
    * ``convert2frame()`` - which converts array of bytes to specific frame.

    Both of these methods must must be implemented for each frame type.

    Following attributes are common for all frame types:

    **Attributes:**

    * ``frame_type`` **(int)** - Defines frame type.
    * ``version`` **(int)** - Standard version. Default value: ``1``.
    * ``pmu_id_code`` **(int)** - Data stream ID number.
    * ``soc`` **(int)** - UNIX timestamp. Default value: ``None``.
    * ``frasec`` **(int)** - Fraction of second and Time Quality. Default value: ``None``.

    **Raises:**

        FrameError
    When it's not possible to create valid frame, usually due invalid parameter value.
    """

    FRAME_TYPES = { "data": 0, "header": 1, "cfg1": 2, "cfg2": 3, "cfg3": 5, "cmd": 4 }

    # Invert FRAME_TYPES codes to get FRAME_TYPE_WORDS
    FRAME_TYPES_WORDS = { code: word for word, code in FRAME_TYPES.items() }
    # {0: 'data', 1: 'header', 2: 'cfg1', 3: 'cfg2', 5: 'cfg3', 4: 'cmd'}


    def __init__(self, frame_type, pmu_id_code, soc=None, frasec=None, version=1):
        """
        CommonFrame abstract class
        :param string frame_type: Defines frame type
        :param int pmu_id_code: Standard version. Default value: ``1``
        :param int soc:
        :param int frasec:
        :param int version:
        :return:
        """

        self.set_frame_type(frame_type)
        self.set_version(version)
        self.set_id_code(pmu_id_code)

        if soc or frasec:
            self.set_time(soc, frasec)


    def set_frame_type(self, frame_type):
        """
        ### set_frame_type() ###

        Setter for ``frame_type``.

        **Params:**

        * ``frame_type`` **(int)** - Should be one of 6 possible values from FRAME_TYPES dict.
        Frame types with integer and binary representations are shown below.
        ______________________________________________________________________________________

            +--------------+----------+-----------+
            |  Frame type  |  Decimal |   Binary  |
            +--------------+----------+-----------+
            | Data         |     0    |    000    |
            +--------------+----------+-----------+
            | Header       |     1    |    001    |
            +--------------+----------+-----------+
            | Config v1    |     2    |    010    |
            +--------------+----------+-----------+
            | Config v2    |     3    |    011    |
            +--------------+----------+-----------+
            | Command      |     4    |    100    |
            +--------------+----------+-----------+
            | Config v3    |     5    |    101    |
            +--------------+----------+-----------+


        **Raises:**

            FrameError
        When ``frame type`` value provided is not specified in ``FRAME_TYPES``.

        """

        if frame_type not in CommonFrame.FRAME_TYPES:
            raise FrameError("Unknown frame type. Possible options: [data, header, cfg1, cfg2, cfg3, cmd].")
        else:
            self._frame_type = CommonFrame.FRAME_TYPES[frame_type]


    def get_frame_type(self):

        return CommonFrame.FRAME_TYPES_WORDS[self._frame_type]


    def extract_frame_type(byte_data):
        """This method will only return type of the frame. It shall be used for stream splitter
        since there is no need to create instance of specific frame which will cause lower performance."""

        # Check if frame is valid
        if not CommandFrame._check_crc(byte_data):
            raise FrameError("CRC failed. Frame not valid.")

        # Get second byte and determine frame type by shifting right to get higher 4 bits
        frame_type = int.from_bytes([byte_data[1]], byteorder="big", signed=False) >> 4

        return CommonFrame.FRAME_TYPES_WORDS[frame_type]


    def set_version(self, version):
        """
        ### set_version() ###

        Setter for frame IEEE standard ``version``.

        **Params:**

        * ``version`` **(int)** - Should be number between ``1`` and ``15``.

        **Raises:**

            FrameError
        When ``version`` value provided is out of range.

        """

        if not 1 <= version <= 15:
            raise FrameError("VERSION number out of range. 1<= VERSION <= 15")
        else:
            self._version = version


    def get_version(self):

        return self._version


    def set_id_code(self, id_code):
        """
        ### set_id_code() ###

        Setter for ``pmu_id_code`` as data stream identified.

        **Params:**

        * ``id_code`` **(int)** - Should be number between ``1`` and ``65534``.

        **Raises:**

            FrameError
        When ``id_code`` value provided is out of range.

        """

        if not 1 <= id_code <= 65534:
            raise FrameError("ID CODE out of range. 1 <= ID_CODE <= 65534")
        else:
            self._pmu_id_code = id_code


    def get_id_code(self):

        return self._pmu_id_code


    def set_time(self, soc=None, frasec=None):
        """
        ### set_time() ###

        Setter for ``soc`` and ``frasec``. If values for ``soc`` or ``frasec`` are
        not provided this method will calculate them.

        **Params:**

        * ``soc`` **(int)** - UNIX timestamp, 32-bit unsigned number. See ``set_soc()``
        method.
        * ``frasec`` **(int)** or **(tuple)** - Fracion of second and Time Quality. See
        ``set_frasec`` method.

        **Raises:**

            FrameError
        When ``soc`` value provided is out of range.

        When ``frasec`` is not valid.

        """

        t = time()  # Get current timestamp

        if soc:
            self.set_soc(soc)
        else:
            self.set_soc(int(t))  # Get current timestamp

        if frasec:
            if isinstance(frasec, collections.Sequence):
                self.set_frasec(*frasec)
            else:
                self.set_frasec(frasec)  # Just set fraction of second and use default values for other arguments.
        else:
            # Calculate fraction of second (after decimal point) using only first 7 digits to avoid
            # overflow (24 bit number).
            self.set_frasec( int( (((repr((t % 1))).split("."))[1])[0:6]) )


    def set_soc(self, soc):
        """
        ### set_soc() ###

        Setter for ``soc`` as second of century.

        **Params:**

        * ``soc`` **(int)** - UNIX timestamp, should be between ``0`` and ``4294967295``.

        **Raises:**

            FrameError
        When ``soc`` value provided is out of range.

        """

        if not 0 <= soc <= 4294967295:
            raise FrameError("Time stamp out of range. 0 <= SOC <= 4294967295")
        else:
            self._soc = soc


    def get_soc(self):

        return self._soc


    def set_frasec(self, fr_seconds, leap_dir="+", leap_occ=False, leap_pen=False, time_quality=0):
        """
        ### set_frasec() ###

        Setter for ``frasec`` as Fraction of Second and Time Quality.

        **Params:**

        *    ``fr_seconds`` **(int)** - Fraction of Second as 24-bit unsigned number.
             Should be between ``0`` and ``16777215``.
        *    ``leap_dir`` **(char)** - Leap Second Direction: ``+`` for add (``0``), ``-`` for
             delete (``1``).
             Default value: ``+``.
        *    ``leap_occ`` **(bool)** - Leap Second Occurred: ``True`` in the first second after
             the leap second occurs and remains set for 24h.
        *    ``leap_pen`` **(bool)** - Leap Second Pending: ``True`` not more than 60 s nor less
             than 1 s before a leap second occurs, and cleared in the second after the leap
             second occurs.
        *    ``time_quality`` **(int)** - Message Time Quality represents worst-case clock
             accuracy according to UTC. Table below shows code values. Should be between ``0``
             and ``15``.
        __________________________________________________________________________________________
            +------------+----------+---------------------------+
            |  Binary    |  Decimal |           Value           |
            +------------+----------+---------------------------+
            | 1111       |    15    | Fault - clock failure.    |
            +------------+----------+---------------------------+
            | 1011       |    11    | Time within 10s of UTC.   |
            +------------+----------+---------------------------+
            | 1010       |    10    | Time within 1s of UTC.    |
            +------------+----------+---------------------------+
            | 1001       |    9     | Time within 10^-1s of UTC.|
            +------------+----------+---------------------------+
            | 1000       |    8     | Time within 10^-2s of UTC.|
            +------------+----------+---------------------------+
            | 0111       |    7     | Time within 10^-3s of UTC.|
            +------------+----------+---------------------------+
            | 0110       |    6     | Time within 10^-4s of UTC.|
            +------------+----------+---------------------------+
            | 0101       |    5     | Time within 10^-5s of UTC.|
            +------------+----------+---------------------------+
            | 0100       |    4     | Time within 10^-6s of UTC.|
            +------------+----------+---------------------------+
            | 0011       |    3     | Time within 10^-7s of UTC.|
            +------------+----------+---------------------------+
            | 0010       |    2     | Time within 10^-8s of UTC.|
            +------------+----------+---------------------------+
            | 0001       |    1     | Time within 10^-9s of UTC.|
            +------------+----------+---------------------------+
            | 0000       |    0     | Clock locked to UTC.      |
            +------------+----------+---------------------------+



        **Raises:**

            FrameError
        When ``fr_seconds`` value provided is out of range.

        When ``time_quality`` value provided is out of range.

        """

        if not 0 <= fr_seconds <= 16777215:
            raise FrameError("Frasec out of range. 0 <= FRASEC <= 16777215 ")

        if (not 0 <= time_quality <= 15) or (time_quality in [12, 13, 14]):
            raise FrameError("Time quality flag out of range. 0 <= MSG_TQ <= 15")

        if leap_dir not in ["+", "-"]:
            raise FrameError("Leap second direction must be '+' or '-'")

        frasec = 1 << 1  # Bit 7: Reserved for future use. Not important but it will be 1 for easier byte forming.

        if leap_dir == "-":  # Bit 6: Leap second direction [+ = 0] and [- = 1].
            frasec |= 1

        frasec <<= 1

        if leap_occ:  # Bit 5: Leap Second Occurred, 1 in first second after leap second, remains 24h.
            frasec |= 1

        frasec <<= 1

        if leap_pen:  # Bit 4: Leap Second Pending - shall be 1 not more then 60s nor less than 1s before leap second.
            frasec |= 1

        frasec <<= 4  # Shift left 4 bits for message time quality

        # Bit 3 - 0: Message Time Quality indicator code - integer representation of bits (check table).
        frasec |= time_quality

        mask = 1 << 7  # Change MSB to 0 for standard compliance.
        frasec ^= mask

        frasec <<= 24  # Shift 24 bits for fractional time.

        frasec |= fr_seconds  # Bits 23-0: Fraction of second.

        self._frasec = frasec


    def get_frasec(self):

        return self._int2frasec(self._frasec)


    @staticmethod
    def _int2frasec(frasec_int):

        tq = frasec_int >> 24
        leap_dir = tq & 0b01000000
        leap_occ = tq & 0b00100000
        leap_pen = tq & 0b00010000

        time_quality = tq & 0b00001111

        # Reassign values to create Command frame
        leap_dir = "-" if leap_dir else "+"
        leap_occ = bool(leap_occ)
        leap_pen = bool(leap_pen)

        fr_seconds = frasec_int & (2**23-1)

        return fr_seconds, leap_dir, leap_occ, leap_pen, time_quality


    @staticmethod
    def _get_data_format_size(data_format):
        """
        ### get_data_format() ###

        Getter for frame data format.

        **Params:**

        * ``data_format`` **(bytes)** - Data format in data frames. Should be 16-bit flag.

        **Returns:**

        * ``dict`` with PHASOR, ANALOG, and FREQ measurement size in bytes.
        ``{'phasor' : phasors_byte_size, 'analog' : analog_byte_size, 'freq' : freq_byte_size}``

        """

        if (data_format & 2) != 0:  # If second bit in data_format is 0 16x2 bits = 4 bytes otherwise 8 (2xfloat).
            phasors_byte_size = 8
        else:
            phasors_byte_size = 4

        if (data_format & 4) != 0:  # If third bit in data_format is 0 16 bits = 2 bytes otherwise 4 bytes (float).
            analog_byte_size = 4
        else:
            analog_byte_size = 2

        if (data_format & 8) != 0:  # If fourth bit in data_format is 0 16 bits = 2 bytes otherwise 4 bytes (float).
            freq_byte_size = 4
        else:
            freq_byte_size = 2

        return { "phasor": phasors_byte_size, "analog": analog_byte_size, "freq": freq_byte_size }


    def set_data_format(self, data_format, num_streams):
        """
        ### set_data_format() ###

        Setter for frame data format. If number of data streams sent by PMUs is larger then
        ``1`` data format should be provided for each data stream. Data format might be
        represented as integer number as shown in table below where ordered letters represent
        ``(PHASOR_RECT/POLAR; PHASOR_INT/FLOAT; ANALOG_INT/FLOAT; FREQ_INT/FLOAT)`` format, where
        ``R`` means RECTANGULAR, ``P`` means POLAR, ``I`` means 16 bit INTEGER and ``F`` means FLOAT.
        Beside this, data format might be provided as tuple of bool values ordered as mentioned
        before.
        __________________________________________________________________________________________

            +--------------+----------+
            |  Data Format |  Decimal |
            +--------------+----------+
            | (R;I;I;I)    |     0    |
            +--------------+----------+
            | (P;I;I;I)    |     1    |
            +--------------+----------+
            | (R;F;I;I)    |     2    |
            +--------------+----------+
            | (P;F;I;I)    |     3    |
            +--------------+----------+
            | (R;I;F;I)    |     4    |
            +--------------+----------+
            | (P;I;F;I)    |     5    |
            +--------------+----------+
            | (R;F;F;I)    |     6    |
            +--------------+----------+
            | (P;F;F;I)    |     7    |
            +--------------+----------+
            | (R;I;I;F)    |     8    |
            +--------------+----------+
            | (P;I;I;F)    |     9    |
            +--------------+----------+
            | (R;F;I;F)    |    10    |
            +--------------+----------+
            | (P;F;I;F)    |    11    |
            +--------------+----------+
            | (R;I;F;F)    |    12    |
            +--------------+----------+
            | (P;I;F;F)    |    13    |
            +--------------+----------+
            | (R;F;F;F)    |    14    |
            +--------------+----------+
            | (P;F;F;F)    |    15    |
            +--------------+----------+

        **Params:**

        * ``data_format`` **(mixed)** - If number of data streams is larger then ``1`` should be list
        of tuples or integers, otherwise single ``tuple`` or ``int`` expected.
        * ``num_streams`` **(int)** - Number of data measurement streams packed in one data frame.

        **Raises:**

            FrameError
        When length of ``data_format`` list is not equal to ``num_stream`` and ``num_stream`` is
        larger then ``1``.

        When ``data_format`` value provided is out of range.

        """

        if num_streams > 1:
            if not isinstance(data_format, list) or num_streams != len(data_format):
                raise FrameError("When NUM_STREAMS > 1 provide FORMATs as list with NUM_STREAMS elements.")

            data_formats = []  # Format tuples transformed to ints
            for format_type in data_format:
                if isinstance(format_type, tuple):  # If data formats are specified as tuples then convert them to ints
                    data_formats.append(CommonFrame._format2int(*format_type))
                else:
                    if not 0 <= format_type <= 15:  # If data formats are specified as ints check range
                        raise FrameError("Format Type out of range. 0 <= FORMAT <= 15")
                    else:
                        data_formats.append(format_type)

                self._data_format = data_formats
        else:
            if isinstance(data_format, tuple):
                self._data_format = CommonFrame._format2int(*data_format)
            else:
                if not 0 <= data_format <= 15:
                    raise FrameError("Format Type out of range. 0 <= FORMAT <= 15")
                self._data_format = data_format


    def get_data_format(self):

        if isinstance(self._data_format, list):
            return [self._int2format(df) for df in self._data_format]
        else:
            return self._int2format(self._data_format)


    @staticmethod
    def _format2int(phasor_polar=False, phasor_float=False, analogs_float=False, freq_float=False):
        """
        ### format2int() ###

        Convert ``boolean`` representation of data format to integer.

        **Params:**

        * ``phasor_polar`` **(bool)** - If ``True`` phasor represented using magnitude and angle (polar)
        else rectangular.
        * ``phasor_float`` **(bool)** - If ``True`` phasor represented using floating point format else
        represented as 16 bit integer.
        * ``analogs_float`` **(bool)** - If ``True`` analog values represented using floating point notation
        else represented as 16 bit integer.
        * ``freq_float`` **(bool)** - If ``True`` FREQ/DFREQ represented using floating point notation
        else represented as 16 bit integer.

        **Returns:**

        * ``int`` representation of data format.

        """

        data_format = 1 << 1

        if freq_float:
            data_format |= 1
        data_format <<= 1

        if analogs_float:
            data_format |= 1
        data_format <<= 1

        if phasor_float:
            data_format |= 1
        data_format <<= 1

        if phasor_polar:
            data_format |= 1

        mask = 1 << 4
        data_format ^= mask

        return data_format


    @staticmethod
    def _int2format(data_format):

        phasor_polar = data_format & 0b0001
        phasor_float = data_format & 0b0010
        analogs_float = data_format & 0b0100
        freq_float = data_format & 0b1000

        return bool(phasor_polar), bool(phasor_float), bool(analogs_float), bool(freq_float)


    @staticmethod
    def _check_crc(byte_data):

        crc_calculated = crc16xmodem(byte_data[0:-2], 0xffff).to_bytes(2, "big")  # Calculate CRC

        if byte_data[-2:] != crc_calculated:
            return False

        return True


    @abstractmethod
    def convert2bytes(self, byte_message):

        # SYNC word in CommonFrame starting with AA hex word + frame type + version
        sync_b = (0xaa << 8) | (self._frame_type << 4) | self._version
        sync_b = sync_b.to_bytes(2, "big")

        # FRAMESIZE: 2B SYNC + 2B FRAMESIZE + 2B IDCODE + 4B SOC + 4B FRASEC + len(Command) + 2B CHK
        frame_size_b = (16 + len(byte_message)).to_bytes(2, "big")

        # PMU ID CODE
        pmu_id_code_b = self._pmu_id_code.to_bytes(2, "big")

        # If timestamp not given set timestamp
        if not hasattr(self, "_soc") and not hasattr(self, "_frasec"):
            self.set_time()
        elif not self._soc and not self._frasec:
            self.set_time()

        # SOC
        soc_b = self._soc.to_bytes(4, "big")

        # FRASEC
        frasec_b = self._frasec.to_bytes(4, "big")

        # CHK
        crc_chk_b = crc16xmodem(sync_b + frame_size_b + pmu_id_code_b + soc_b + frasec_b + byte_message, 0xffff)

        return sync_b + frame_size_b + pmu_id_code_b + soc_b + frasec_b + byte_message + crc_chk_b.to_bytes(2, "big")


    @abstractmethod
    def convert2frame(byte_data, cfg=None):

        convert_method = {
            0: DataFrame.convert2frame,
            1: HeaderFrame.convert2frame,
            2: ConfigFrame1.convert2frame,
            3: ConfigFrame2.convert2frame,
            4: CommandFrame.convert2frame,
            5: ConfigFrame3.convert2frame,
        }

        if not CommonFrame._check_crc(byte_data):
            raise FrameError("CRC failed. Frame not valid.")

        # Get second byte and determine frame type by shifting right to get higher 4 bits
        frame_type = int.from_bytes([byte_data[1]], byteorder="big", signed=False) >> 4

        if frame_type == 0:  # DataFrame pass Configuration to decode message
            return convert_method[frame_type](byte_data, cfg)

        return convert_method[frame_type](byte_data)


class DataFrame(CommonFrame):

    MEASUREMENT_STATUS = { "ok": 0, "error": 1, "test": 2, "verror": 3 }
    MEASUREMENT_STATUS_WORDS = { code: word for word, code in MEASUREMENT_STATUS.items() }

    UNLOCKED_TIME = { "<10": 0, "<100": 1, "<1000": 2, ">1000": 3 }
    UNLOCKED_TIME_WORDS = { code: word for word, code in UNLOCKED_TIME.items() }

    TIME_QUALITY = { "n/a": 0, "<100ns": 1, "<1us": 2, "<10us": 3, "<100us": 4, "<1ms": 5, "<10ms": 6, ">10ms": 7}
    TIME_QUALITY_WORDS = { code: word for word, code in TIME_QUALITY.items() }

    TRIGGER_REASON = { "manual": 0, "magnitude_low": 1, "magnitude_high": 2, "phase_angle_diff": 3,
                       "frequency_high_or_log": 4, "df/dt_high": 5, "reserved": 6, "digital": 7 }
    TRIGGER_REASON_WORDS = { code: word for word, code in TRIGGER_REASON.items() }


    def __init__(self, pmu_id_code, stat, phasors, freq, dfreq, analog, digital, cfg, soc=None, frasec=None):

        if not isinstance(cfg, ConfigFrame2):
            raise FrameError("CFG should describe current data stream (ConfigurationFrame2)")

        # Common frame for Configuration frame 2 with PMU simulator ID CODE which sends configuration frame.
        super().__init__("data", pmu_id_code, soc, frasec)

        self.cfg = cfg
        self.set_stat(stat)
        self.set_phasors(phasors)
        self.set_freq(freq)
        self.set_dfreq(dfreq)
        self.set_analog(analog)
        self.set_digital(digital)


    def set_stat(self, stat):

        if self.cfg._num_pmu > 1:
            if not isinstance(stat, list) or self.cfg._num_pmu != len(stat):
                raise TypeError("When number of measurements > 1 provide STAT as list with NUM_MEASUREMENTS elements.")

            stats = []  # Format tuples transformed to ints
            for stat_el in stat:
                # If stat is specified as tuple then convert them to int
                if isinstance(stat_el, tuple):
                    stats.append(DataFrame._stat2int(*stat_el))
                else:
                    # If data formats are specified as ints check range
                    if not 0 <= stat_el <= 65536:
                        raise ValueError("STAT out of range. 0 <= STAT <= 65536")
                    else:
                        stats.append(stat_el)

                self._stat = stats
        else:
            if isinstance(stat, tuple):
                self._stat = DataFrame._stat2int(*stat)
            else:
                if not 0 <= stat <= 65536:
                    raise ValueError("STAT out of range. 0 <= STAT <= 65536")
                else:
                    self._stat = stat


    def get_stat(self):

        if isinstance(self._stat, list):
            return [DataFrame._int2stat(stat) for stat in self._stat]
        else:
            return DataFrame._int2stat(self._stat)


    @staticmethod
    def _stat2int(measurement_status="ok", sync=True, sorting="timestamp", trigger=False, cfg_change=False,
                  modified=False, time_quality=5, unlocked="<10", trigger_reason=0):

        if isinstance(measurement_status, str):
            measurement_status = DataFrame.MEASUREMENT_STATUS[measurement_status]

        if isinstance(time_quality, str):
            time_quality = DataFrame.TIME_QUALITY[time_quality]

        if isinstance(unlocked, str):
            unlocked = DataFrame.UNLOCKED_TIME[unlocked]

        if isinstance(trigger_reason, str):
            trigger_reason = DataFrame.TRIGGER_REASON[trigger_reason]

        stat = measurement_status << 2
        if not sync:
            stat |= 1

        stat <<= 1
        if not sorting == "timestamp":
            stat |= 1

        stat <<= 1

        if trigger:
            stat |= 1
        stat <<= 1

        if cfg_change:
            stat |= 1

        stat <<= 1

        if modified:
            stat |= 1

        stat <<= 3
        stat |= time_quality
        stat <<= 2

        stat |= unlocked
        stat <<= 4

        return stat | trigger_reason


    @staticmethod
    def _int2stat(stat):

        measurement_status = DataFrame.MEASUREMENT_STATUS_WORDS[stat >> 15]
        sync = bool(stat & 0x2000)

        if stat & 0x1000:
            sorting = "arrival"
        else:
            sorting = "timestamp"

        trigger = bool(stat & 0x800)
        cfg_change = bool(stat & 0x400)
        modified = bool(stat & 0x200)

        time_quality = DataFrame.TIME_QUALITY_WORDS[stat & 0x1c0]
        unlocked = DataFrame.UNLOCKED_TIME_WORDS[stat & 0x30]
        trigger_reason = DataFrame.TRIGGER_REASON_WORDS[stat & 0xf]

        return measurement_status, sync, sorting, trigger, cfg_change, modified, time_quality, unlocked, trigger_reason


    def set_phasors(self, phasors):

        phasors_list = []  # Format tuples transformed to ints
        if self.cfg._num_pmu > 1:
            if not isinstance(phasors, list) or self.cfg._num_pmu != len(phasors):
                raise TypeError("When number of measurements > 1 provide PHASORS as list of tuple list with "
                                "NUM_MEASUREMENTS elements.")

            if not isinstance(self.cfg._data_format, list) or self.cfg._num_pmu != len(self.cfg._data_format):
                raise TypeError("When number of measurements > 1 provide DATA_FORMAT as list with "
                                "NUM_MEASUREMENTS elements.")

            for i, phasor in enumerate(phasors):

                if not isinstance(phasor, list) or self.cfg._phasor_num[i] != len(phasor):
                    raise TypeError("Provide PHASORS as list of tuples with PHASOR_NUM tuples")

                ph_measurements = []
                for phasor_measurement in phasor:
                    ph_measurements.append(DataFrame._phasor2int(phasor_measurement, self.cfg._data_format[i]))

                phasors_list.append(ph_measurements)
        else:

            if not isinstance(phasors, list) or self.cfg._phasor_num != len(phasors):
                raise TypeError("Provide PHASORS as list of tuples with PHASOR_NUM tuples")

            for phasor_measurement in phasors:
                phasors_list.append(DataFrame._phasor2int(phasor_measurement, self.cfg._data_format))

        self._phasors = phasors_list


    def get_phasors(self, convert2polar=True):

        if all(isinstance(el, list) for el in self._phasors):

            phasors = [[DataFrame._int2phasor(ph, self.cfg._data_format[i]) for ph in phasor]
                       for i, phasor in enumerate(self._phasors)]

            if convert2polar:
                for i, stream_phasors in enumerate(phasors):

                    if not self.cfg.get_data_format()[i][1]:  # If not float representation scale back
                        stream_phasors = [tuple([ph*self.cfg.get_ph_units()[i][j][0]*0.00001 for ph in phasor]) 
                                          for j, phasor in enumerate(stream_phasors)]

                        phasors[i] = stream_phasors

                    if not self.cfg.get_data_format()[i][0]:  # If not polar convert to polar representation
                        stream_phasors = [(sqrt(ph[0]**2 + ph[1]**2), atan2(ph[1], ph[0])) for ph in stream_phasors]
                        phasors[i] = stream_phasors
        else:
            phasors = [DataFrame._int2phasor(phasor, self.cfg._data_format) for phasor in self._phasors]

            if not self.cfg.get_data_format()[1]:  # If not float representation scale back
                phasors = [tuple([ph*self.cfg.get_ph_units()[i][0]*0.00001 for ph in phasor]) 
                           for i, phasor in enumerate(phasors)]

            if not self.cfg.get_data_format()[0]:  # If not polar convert to polar representation
                phasors = [(sqrt(ph[0]**2 + ph[1]**2), atan2(ph[1], ph[0])) for ph in phasors]

        return phasors

    @staticmethod
    def _phasor2int(phasor, data_format):

        if not isinstance(phasor, tuple):
            raise TypeError("Provide phasor measurement as tuple. Rectangular - (Re, Im); Polar - (Mg, An).")

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[0]:  # Polar representation

            if data_format[1]:  # Floating Point

                if not -3.142 <= phasor[1] <= 3.142:
                    raise ValueError("Angle must be in range -3.14 <= ANGLE <= 3.14")

                mg = pack("!f", float(phasor[0]))
                an = pack("!f", float(phasor[1]))
                measurement = mg + an

            else:  # Polar 16-bit representations

                if not 0 <= phasor[0] <= 65535:
                    raise ValueError("Magnitude must be 16-bit unsigned integer. 0 <= MAGNITUDE <= 65535.")

                if not -31416 <= phasor[1] <= 31416:
                    raise ValueError("Angle must be 16-bit signed integer in radians x (10^-4). "
                                     "-31416 <= ANGLE <= 31416.")

                mg = pack("!H", phasor[0])
                an = pack("!h", phasor[1])
                measurement = mg + an

        else:

            if data_format[1]:  # Rectangular floating point representation

                re = pack("!f", float(phasor[0]))
                im = pack("!f", float(phasor[1]))
                measurement = re + im

            else:

                if not ((-32767 <= phasor[0] <= 32767) or (-32767 <= phasor[1] <= 32767)):
                    raise ValueError("Real and imaginary value must be 16-bit signed integers. "
                                     "-32767 <= (Re,Im) <= 32767.")

                re = pack("!h", phasor[0])
                im = pack("!h", phasor[1])
                measurement = re + im

        return int.from_bytes(measurement, "big", signed=False)


    @staticmethod
    def _int2phasor(phasor, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[1]:  # Float representation
            phasor = unpack("!ff", phasor.to_bytes(8, "big", signed=False))
        elif data_format[0]:  # Polar integer
            phasor = unpack("!Hh", phasor.to_bytes(4, "big", signed=False))
        else:  # Rectangular integer
            phasor = unpack("!hh", phasor.to_bytes(4, "big", signed=False))

        return phasor


    def set_freq(self, freq):

        if self.cfg._num_pmu > 1:
            if not isinstance(freq, list) or self.cfg._num_pmu != len(freq):
                raise TypeError("When number of measurements > 1 provide FREQ as list with "
                                "NUM_MEASUREMENTS elements.")

            if not isinstance(self.cfg._data_format, list) or self.cfg._num_pmu != len(self.cfg._data_format):
                raise TypeError("When number of measurements > 1 provide DATA_FORMAT as list with "
                                "NUM_MEASUREMENTS elements.")

            freq_list = []  # Format tuples transformed to ints
            for i, fr in enumerate(freq):
                freq_list.append(DataFrame._freq2int(fr, self.cfg._data_format[i]))

            self._freq = freq_list
        else:
            self._freq = DataFrame._freq2int(freq, self.cfg._data_format)


    def get_freq(self):

        if isinstance(self._freq, list):
            freq = [DataFrame._int2freq(fr, self.cfg._data_format[i]) for i, fr in enumerate(self._freq)]
        else:
            freq = DataFrame._int2freq(self._freq, self.cfg._data_format)

        return freq


    def _freq2int(freq, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[3]:  # FREQ/DFREQ floating point
            if not -32.767 <= freq <= 32.767:
                raise ValueError("FREQ must be in range -32.767 <= FREQ <= 32.767.")

            freq = unpack("!I", pack("!f", float(freq)))[0]
        else:
            if not -32767 <= freq <= 32767:
                raise ValueError("FREQ must be 16-bit signed integer. -32767 <= FREQ <= 32767.")
            freq = unpack("!H", pack("!h", freq))[0]

        return freq


    def _int2freq(freq, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[3]:  # FREQ/DFREQ floating point
            freq = unpack("!f", pack("!I", freq))[0]
        else:
            freq = unpack("!h", pack("!H", freq))[0]

        return freq


    def set_dfreq(self, dfreq):

        if self.cfg._num_pmu > 1:
            if not isinstance(dfreq, list) or self.cfg._num_pmu != len(dfreq):
                raise TypeError("When number of measurements > 1 provide DFREQ as list with "
                                "NUM_MEASUREMENTS elements.")

            if not isinstance(self.cfg._data_format, list) or self.cfg._num_pmu != len(self.cfg._data_format):
                raise TypeError("When number of measurements > 1 provide DATA_FORMAT as list with "
                                "NUM_MEASUREMENTS elements.")

            dfreq_list = []  # Format tuples transformed to ints
            for i, dfr in enumerate(dfreq):
                dfreq_list.append(DataFrame._dfreq2int(dfr, self.cfg._data_format[i]))

            self._dfreq = dfreq_list
        else:
            self._dfreq = DataFrame._dfreq2int(dfreq, self.cfg._data_format)


    def get_dfreq(self):

        if isinstance(self._dfreq, list):
            dfreq = [DataFrame._int2dfreq(dfr, self.cfg._data_format[i]) for i, dfr in enumerate(self._dfreq)]
        else:
            dfreq = DataFrame._int2dfreq(self._dfreq, self.cfg._data_format)

        return dfreq


    def _dfreq2int(dfreq, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[3]:  # FREQ/DFREQ floating point
            dfreq = unpack("!I", pack("!f", float(dfreq)))[0]
        else:
            if not -32767 <= dfreq <= 32767:
                raise ValueError("DFREQ must be 16-bit signed integer. -32767 <= DFREQ <= 32767.")
            dfreq = unpack("!H", pack("!h", dfreq))[0]

        return dfreq


    def _int2dfreq(dfreq, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[3]:  # FREQ/DFREQ floating point
            dfreq = unpack("!f", pack("!I", dfreq))[0]
        else:
            dfreq = unpack("!h", pack("!H", dfreq))[0]

        return dfreq


    def set_analog(self, analog):

        analog_list = []
        # Format tuples transformed to ints
        if self.cfg._num_pmu > 1:
            if not isinstance(analog, list) or self.cfg._num_pmu != len(analog):
                raise TypeError("When number of measurements > 1 provide ANALOG as list of list with "
                                "NUM_MEASUREMENTS elements.")

            if not isinstance(self.cfg._data_format, list) or self.cfg._num_pmu != len(self.cfg._data_format):
                raise TypeError("When number of measurements > 1 provide DATA_FORMAT as list with "
                                "NUM_MEASUREMENTS elements.")

            for i, an in enumerate(analog):

                if not isinstance(an, list) or self.cfg._analog_num[i] != len(an):
                    raise TypeError("Provide ANALOG as list with ANALOG_NUM elements")

                an_measurements = []
                for analog_measurement in an:
                    an_measurements.append(DataFrame._analog2int(analog_measurement, self.cfg._data_format[i]))

                analog_list.append(an_measurements)

        else:

            if not isinstance(analog, list) or self.cfg._analog_num!= len(analog):
                    raise TypeError("Provide ANALOG as list with ANALOG_NUM elements")

            for analog_measurement in analog:
                analog_list.append(DataFrame._analog2int(analog_measurement, self.cfg._data_format))

        self._analog = analog_list


    def get_analog(self):

        if all(isinstance(el, list) for el in self._analog):
            analog = [[DataFrame._int2analog(an, self.cfg._data_format[i]) for an in analog]
                      for i, analog in enumerate(self._analog)]
        else:
            analog = [DataFrame._int2analog(an, self.cfg._data_format) for an in self._analog]

        return analog


    def _analog2int(analog, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[2]:  # ANALOG float
            analog = unpack("!I", pack("!f", float(analog)))[0]
        else:
            # User defined ranges - but fit in 16-bit (u)signed integer
            if not -32767 <= analog <= 32767:
                raise ValueError("ANALOG must be in range -32767 <= FREQ <= 65535.")
            analog = unpack("!H", pack("!h", analog))[0]

        return analog


    def _int2analog(analog, data_format):

        if isinstance(data_format, int):
            data_format = DataFrame._int2format(data_format)

        if data_format[2]:  # ANALOG float
            analog = unpack("!f", pack("!I", analog))[0]
        else:
            analog = unpack("!h", pack("!H", analog))[0]

        return analog


    def set_digital(self, digital):

        digital_list = []
        # Format tuples transformed to ints
        if self.cfg._num_pmu > 1:
            if not isinstance(digital, list) or self.cfg._num_pmu != len(digital):
                raise TypeError("When number of measurements > 1 provide DIGITAL as list of lists with "
                                "NUM_MEASUREMENTS elements.")

            for i, dig in enumerate(digital):

                if not isinstance(dig, list) or self.cfg._digital_num[i] != len(dig):
                    raise TypeError("Provide DIGITAL as list with DIGITAL_NUM elements")

                dig_measurements = []
                for digital_measurement in dig:
                    dig_measurements.append(DataFrame._digital2int(digital_measurement))

                digital_list.append(dig_measurements)

        else:

            if not isinstance(digital, list) or self.cfg._digital_num != len(digital):
                    raise TypeError("Provide DIGITAL as list with DIGITAL_NUM elements")

            for digital_measurement in digital:
                digital_list.append(DataFrame._digital2int(digital_measurement))

        self._digital = digital_list


    def get_digital(self):

        return self._digital


    def _digital2int(digital):

        if not -32767 <= digital <= 65535:
            raise ValueError("DIGITAL must be 16 bit word. -32767 <= DIGITAL <= 65535.")
        return unpack("!H", pack("!H", digital))[0]


    def get_measurements(self):

        measurements = []

        if self.cfg._num_pmu > 1:

            frequency = [self.cfg.get_fnom()[i] + freq / 1000 for i, freq in enumerate(self.get_freq())]

            for i in range(self.cfg._num_pmu):

                measurement = { "stream_id": self.cfg.get_stream_id_code()[i],
                                "stat": self.get_stat()[i][0],
                                "phasors": self.get_phasors()[i],
                                "analog": self.get_analog()[i],
                                "digital": self.get_digital()[i],
                                "frequency": self.cfg.get_fnom()[i] + self.get_freq()[i] / 1000,
                                "rocof": self.get_dfreq()[i]}

                measurements.append(measurement)
        else:

            measurements.append({ "stream_id": self.cfg.get_stream_id_code(),
                                  "stat": self.get_stat()[0],
                                  "phasors": self.get_phasors(),
                                  "analog": self.get_analog(),
                                  "digital": self.get_digital(),
                                  "frequency": self.cfg.get_fnom() + self.get_freq() / 1000,
                                  "rocof": self.get_dfreq()
                                })

        data_frame = { "pmu_id": self._pmu_id_code,
                       "time": self.get_soc() + self.get_frasec()[0] / self.cfg.get_time_base(),
                       "measurements": measurements }

        return data_frame


    def convert2bytes(self):

        # Convert DataFrame message to bytes
        if not self.cfg._num_pmu > 1:

            data_format_size = CommonFrame._get_data_format_size(self.cfg._data_format)

            df_b = self._stat.to_bytes(2, "big") + list2bytes(self._phasors, data_format_size["phasor"]) + \
                   self._freq.to_bytes(data_format_size["freq"], "big") + \
                   self._dfreq.to_bytes(data_format_size["freq"], "big") + \
                   list2bytes(self._analog, data_format_size["analog"]) + list2bytes(self._digital, 2)
        else:
            # Concatenate measurements as many as num_measurements tells
            df_b = None
            for i in range(self.cfg._num_pmu):

                data_format_size = CommonFrame._get_data_format_size(self.cfg._data_format[i])

                df_b_i = self._stat[i].to_bytes(2, "big") + \
                         list2bytes(self._phasors[i], data_format_size["phasor"]) + \
                         self._freq[i].to_bytes(data_format_size["freq"], "big") + \
                         self._dfreq[i].to_bytes(data_format_size["freq"], "big") + \
                         list2bytes(self._analog[i], data_format_size["analog"]) + \
                         list2bytes(self._digital[i], 2)

                if df_b:
                    df_b += df_b_i
                else:
                    df_b = df_b_i

        return super().convert2bytes(df_b)


    @staticmethod
    def convert2frame(byte_data, cfg):

        try:

            if not CommonFrame._check_crc(byte_data):
                raise FrameError("CRC failed. Configuration frame not valid.")

            num_pmu = cfg.get_num_pmu()
            data_format = cfg.get_data_format()
            phasor_num = cfg.get_phasor_num()
            analog_num = cfg.get_analog_num()
            digital_num = cfg.get_digital_num()

            pmu_code = int.from_bytes(byte_data[4:6], byteorder="big", signed=False)
            soc = int.from_bytes(byte_data[6:10], byteorder="big", signed=False)
            frasec = CommonFrame._int2frasec(int.from_bytes(byte_data[10:14], byteorder="big", signed=False))

            start_byte = 14

            if num_pmu > 1:

                stat, phasors, freq, dfreq, analog, digital = [[] for _ in range(6)]

                for i in range(num_pmu):

                    st = DataFrame._int2stat(int.from_bytes(byte_data[start_byte:start_byte+2],
                                                            byteorder="big", signed=False))
                    stat.append(st)
                    start_byte += 2

                    phasor_size = 8 if data_format[i][1] else 4
                    stream_phasors = []
                    for _ in range(phasor_num[i]):
                        phasor = DataFrame._int2phasor(int.from_bytes(byte_data[start_byte:start_byte+phasor_size],
                                                                      byteorder="big", signed=False), data_format[i])
                        stream_phasors.append(phasor)
                        start_byte += phasor_size
                    phasors.append(stream_phasors)

                    freq_size = 4 if data_format[i][3] else 2
                    stream_freq = DataFrame._int2freq(int.from_bytes(byte_data[start_byte:start_byte+freq_size],
                                                                     byteorder="big", signed=False), data_format[i])
                    start_byte += freq_size
                    freq.append(stream_freq)

                    stream_dfreq = DataFrame._int2dfreq(int.from_bytes(byte_data[start_byte:start_byte+freq_size],
                                                                       byteorder="big", signed=False), data_format[i])
                    start_byte += freq_size
                    dfreq.append(stream_dfreq)

                    analog_size = 4 if data_format[i][2] else 2
                    stream_analog = []
                    for _ in range(analog_num[i]):
                        an = DataFrame._int2analog(int.from_bytes(byte_data[start_byte:start_byte+analog_size],
                                                                  byteorder="big", signed=False), data_format[i])
                        stream_analog.append(an)
                        start_byte += analog_size
                    analog.append(stream_analog)

                    stream_digital = []
                    for _ in range(digital_num[i]):
                        dig = int.from_bytes(byte_data[start_byte:start_byte+2], byteorder="big", signed=False)
                        stream_digital.append(dig)
                        start_byte += 2
                    digital.append(stream_digital)
            else:

                stat = DataFrame._int2stat(int.from_bytes(byte_data[start_byte:start_byte+2],
                                                          byteorder="big", signed=False))
                start_byte += 2

                phasor_size = 8 if data_format[1] else 4
                phasors = []
                for _ in range(phasor_num):
                    phasor = DataFrame._int2phasor(int.from_bytes(byte_data[start_byte:start_byte+phasor_size],
                                                                  byteorder="big", signed=False), data_format)
                    phasors.append(phasor)
                    start_byte += phasor_size

                freq_size = 4 if data_format[3] else 2
                freq = DataFrame._int2freq(int.from_bytes(byte_data[start_byte:start_byte+freq_size],
                                                          byteorder="big", signed=False), data_format)
                start_byte += freq_size

                dfreq = DataFrame._int2dfreq(int.from_bytes(byte_data[start_byte:start_byte+freq_size], byteorder="big",
                                                            signed=False), data_format)
                start_byte += freq_size

                analog_size = 4 if data_format[2] else 2
                analog = []
                for _ in range(analog_num):
                    an = DataFrame._int2analog(int.from_bytes(byte_data[start_byte:start_byte+analog_size],
                                                                  byteorder="big", signed=False), data_format)
                    analog.append(an)
                    start_byte += analog_size

                digital = []
                for _ in range(digital_num):
                    dig = int.from_bytes(byte_data[start_byte:start_byte+2], byteorder="big", signed=False)
                    digital.append(dig)
                    start_byte += 2

            return DataFrame(pmu_code, stat, phasors, freq, dfreq, analog, digital, cfg, soc, frasec)

        except Exception as error:
            raise FrameError("Error while creating Data frame: " + str(error))

class FrameError(BaseException):
    pass
