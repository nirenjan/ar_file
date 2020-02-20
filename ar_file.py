"""
:mod:`ar_file` -- Unix Archive file access library
==================================================

.. module:: ar_file
.. module_author:: Nirenjan Krishnan <nirenjan@gmail.com>
"""

#######################################################################
# ar_file constants
#######################################################################

# Formats that ar_file supports
GNU_FORMAT = 1  # GNU format, using /<n> for extended filenames
BSD_FORMAT = 2  # BSD format, using #1/<n> for extended filenames

DEFAULT_FORMAT = GNU_FORMAT

# Default encoding - always use UTF-8
ENCODING = 'utf-8'

#######################################################################
# ar_file Exceptions
#######################################################################

class ArError(Exception):
    """Base class for all ar_file exceptions"""

class ReadError(ArError):
    """Is raised when an AR file is opened, that either cannot be handled
    by the ar_file module or is somehow invalid."""

class StreamError(ArError):
    """Is raised for the limitations that are typical for stream-like
    ArFile objects"""

class ExtractError(ArError):
    """Is raised for extraction errors when using ArFile.extract()"""

class HeaderError(ArError):
    """Is raised by ArInfo.frombuf() if the buffer it gets is invalid"""

class EncodingError(ArError):
    """Is raised by ArInfo.tobuf() if it cannot encode the content within
    the given header"""

#######################################################################
# ar_file ArInfo class
#######################################################################

class ArInfo():
    """An ArInfo object represents one member in an ArFile. Aside from
    storing all required attributes of a file (like filename, size,
    ownership, time), it provides some useful methods to extract it from
    the ArFile. It does not contain the file's data itself.
    """

    def __init__(self, name=''):
        """Create an ArInfo object"""
        self.name = name
        self.mtime = 0
        self.uid = 0
        self.gid = 0
        self.mode = 0o000644
        self.size = 0

        # Additional attributes
        self._stream_fd = None
        self._stream_offs = 0
        self._parent = None
        self._inline_name = False

    def tobuf(self, format=DEFAULT_FORMAT, encoding=ENCODING, errors='strict'):
        """Create a string buffer of an ArInfo object."""
        if format == BSD_FORMAT:
            return self._create_bsd_format(encoding, errors)

        if format == GNU_FORMAT:
            return self._create_gnu_format(encoding, errors)

        return EncodingError(f"Invalid format {format}")

    @classmethod
    def frombuf(cls, buf, arfile=None, encoding=ENCODING, errors='strict'):
        """Create an ArInfo object from the string representation"""
        if not isinstance(buf, bytes):
            raise HeaderError("Invalid type of buf - expected bytes")

        buf = buf.decode(encoding, errors)

        # Verify that the length is at least 60 bytes
        if len(buf) < 60:
            raise HeaderError("Invalid buf, too short")

        name = buf[0:16].rstrip()

        def parse_int(field, value, base=10):
            """Parse an integer field and return the value"""
            try:
                return int(value, base)
            except ValueError:
                raise HeaderError(f"Invalid numeric field {value} for {field}")

            return None

        mtime = parse_int('mtime', buf[16:28])
        uid = parse_int('uid', buf[28:34])
        gid = parse_int('gid', buf[34:40])
        mode = parse_int('file mode', buf[40:48], 8)
        size = parse_int('size', buf[48:58], 8)

        if buf[58:60] != '\x60\x0a':
            raise HeaderError("Invalid buffer format, invalid terminator")

        info_obj = cls(name)
        info_obj.mtime = mtime
        info_obj.uid = uid
        info_obj.gid = gid
        info_obj.mode = mode
        info_obj.size = size

        # Set the pointer to the parent ArFile
        info_obj._parent = arfile

        # Parse the filename format
        special = name.startswith('/') or name.startswith('#1/')
        if special:
            info_obj._inline_filename = name.startswith('#1/')

        if special and info_obj._inline_filename:
            # BSD Format
            try:
                length = int(name[3:], 10)
            except ValueError:
                raise HeaderError(f"Invalid filename {name}")

            if len(buf) >= (60 + length):
                # We have enough data to get the filename
                info_obj.name = buf[60:60+length]

        if special and not info_obj._inline_filename:
            # GNU Format
            try:
                offset = int(name[1:], 10)
            except ValueError:
                raise HeaderError(f"Invalid filename {name}")

            if arfile is None:
                raise HeaderError(
                        f"Unable to convert filename {name}, need ArFile")

            # Get the filename from the ArFile object
            info_obj.name = arfile.read_filename(offset)

    def _append_common_data(self):
        text = ''
        # Insert file modification timestamp
        text += '{:<12d}'.format(self.mtime)

        # Insert UID & GID
        text += '{:<6d}'.format(self.uid)
        text += '{:<6d}'.format(self.gid)

        # Insert file mode
        text += '{:<8o}'.format(self.mode)

        # Insert file size
        text += '{:<10d}'.format(self.size)

        # Insert ending characters
        text += '\x60\x0a'

        return text

    def _create_bsd_format(self, encoding, errors):
        # Insert filename
        if len(self.name) <= 16:
            text = self.name.ljust(16)
        else:
            text = f'#1/{len(self.name)}'.ljust(16)
            self._inline_name = True

        text += self._append_common_data()

        return text.encode(encoding, errors)

    def _create_gnu_format(self, encoding, errors):
        # Insert filename
        if len(self.name) <= 15:
            text = (self.name + '/').ljust(16)
        else:
            if self._parent is None:
                raise EncodingError("Unable to save extended filename")

            offset = self._parent.save_filename(self.name)
            text = f'/{offset}'.ljust(16)

        text += self._append_common_data()

        return text.encode(encoding, errors)

#######################################################################
# ar_file ArFile class
#######################################################################

class ArFile():
    """TODO:"""
