"""
Consistent Overhead Byte Stuffing (COBS)

Unit Tests specific to the C implementation details.
In particular, test output buffer overflow detection.

This version is for Python 2.x.
"""

from array import array
import ctypes
import sys
import unittest

from cobs import cobs
#from cobs.cobs import _cobs_py as cobs
import cobs_wrapper


def infinite_non_zero_generator():
    while True:
        for i in xrange(1,50):
            for j in xrange(1,256, i):
                yield j

def non_zero_generator(length):
    non_zeros = infinite_non_zero_generator()
    for i in xrange(length):
        yield non_zeros.next()

def non_zero_bytes(length):
    return ''.join(chr(i) for i in non_zero_generator(length))


class OutputOverflowTests(unittest.TestCase):
    predefined_encodings = [
        [ "",                                       "\x01"                                                          ],
        [ "1",                                      "\x021"                                                         ],
        [ "12345",                                  "\x0612345"                                                     ],
        [ "12345\x006789",                          "\x0612345\x056789"                                             ],
        [ "\x0012345\x006789",                      "\x01\x0612345\x056789"                                         ],
        [ "12345\x006789\x00",                      "\x0612345\x056789\x01"                                         ],
        [ "\x00",                                   "\x01\x01"                                                      ],
        [ "\x00\x00",                               "\x01\x01\x01"                                                  ],
        [ "\x00\x00\x00",                           "\x01\x01\x01\x01"                                              ],
        [ array('B', range(1, 254)).tostring(),     "\xfe" + array('B', range(1, 254)).tostring()                   ],
        [ array('B', range(1, 255)).tostring(),     "\xff" + array('B', range(1, 255)).tostring()                   ],
        [ array('B', range(1, 256)).tostring(),     "\xff" + array('B', range(1, 255)).tostring() + "\x02\xff"      ],
        [ array('B', range(0, 256)).tostring(),     "\x01\xff" + array('B', range(1, 255)).tostring() + "\x02\xff"  ],
    ]

    def test_encode_output_overflow(self):
        for (test_string, expected_encoded_string) in self.predefined_encodings:
            try:
                real_out_buffer_len = cobs_wrapper.encode_size_max(len(test_string)) + 100
    
                for out_buffer_len in xrange(0, real_out_buffer_len + 1):
    
                    out_buffer = ctypes.create_string_buffer('\xAA' * real_out_buffer_len, real_out_buffer_len)
    
                    ret_val = cobs_wrapper.encode_cfunc(out_buffer, out_buffer_len, test_string, len(test_string))
    
                    if out_buffer_len < len(expected_encoded_string):
                        # Check that the output buffer overflow error status is flagged
                        self.assertTrue((ret_val.status & cobs_wrapper.CobsEncodeStatus.OUT_BUFFER_OVERFLOW) != 0)
                        self.assertEqual(ret_val.out_len, out_buffer_len)
                        actual_decoded = cobs.decode(out_buffer[:ret_val.out_len])
                        self.assertTrue(test_string.startswith(actual_decoded),
                                        "for %s, encode buffer length %d, got %s" % (repr(test_string), out_buffer_len, repr(actual_decoded)))
    
                    if out_buffer_len >= len(expected_encoded_string):
                        # Check that the output buffer overflow error status is NOT flagged
                        self.assertTrue((ret_val.status & cobs_wrapper.CobsEncodeStatus.OUT_BUFFER_OVERFLOW) == 0)
                        # Check that the correct encoded value is returned
#                        self.assertEqual(ret_val.out_len, len(expected_encoded_string))
                        self.assertEqual(out_buffer[:ret_val.out_len], expected_encoded_string)
    
                    self.assertEqual(out_buffer[ret_val.out_len:], '\xAA' * (real_out_buffer_len - ret_val.out_len))
            except AssertionError:
                print >> sys.stderr, "For test string %s" % repr(test_string)
                raise


def runtests():
    unittest.main()


if __name__ == '__main__':
    runtests()