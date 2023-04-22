import logging
from typing import List, Tuple

from serial import Serial


logger = logging.getLogger(__name__)


class CO2Sensor:
    """
    MH-Z16 and MH-Z19 CO2 sensor.
    """

    serial: Serial

    def __init__(
            self,
            port: str,
            baudrate: int = 9600,
            timeout: float = 0.2,
    ):
        """
        Setup CO2 sensor

        :param port: The serial port name, for example `/dev/ttyUSB0` (Linux),
                        `/dev/tty.usbserial` (OS X) or `COM4` (Windows).
        :param baudrate: Baudrate to use.
        :param timeout: Read timeout after each command.
        """
        self.serial = Serial(port=port, baudrate=baudrate, timeout=timeout)
        self.serial.open()

    READ_CO2 = [0xff, 0x01, 0x86, 0x00, 0x00, 0x00, 0x00, 0x00]
    ZERO_CALIBRATION = [0xff, 0x01, 0x87, 0x00, 0x00, 0x00, 0x00, 0x00]
    SPAN_CALIBRATION = [0xff, 0x01, 0x88, 0x00, 0x00, 0x00, 0x00, 0x00]
    AUTO_CALIBRATION = [0xff, 0x01, 0x79, 0xa0, 0x00, 0x00, 0x00, 0x00]
    AUTO_CALIBRATION_OFF = [0xff, 0x01, 0x79, 0x00, 0x00, 0x00, 0x00, 0x00]

    @staticmethod
    def _checksum(data: bytes | List[int]) -> int:
        """
        Calculate _checksum of the command.
        """
        return 0xff - (sum(data) % 256) + 1

    def _write_command(self, command: List[int]):
        """
        Write command to the sensor.
        """
        command.append(self._checksum(command))
        self.serial.write(command)

    def _read_response(self) -> bytes:
        """
        Read response from the sensor.
        """
        return self.serial.read(9)

    def read_co2(self) -> int:
        """
        Read CO2 concentration.
        """
        return self.read()[0]

    def read_temperature(self) -> float:
        """
        Read temperature.
        """
        return self.read()[1]

    def read_status(self) -> int:
        """
        Read status.
        """
        return self.read()[2]

    def read(self) -> Tuple[int, float, int, int]:
        """
        Read all values.

        :note: last value is auto calibration point, see
        :link: https://revspace.nl/MH-Z19#Command_set

        :return: CO2 concentration, temperature, status, co2 auto calibration point
        """
        self._write_command(self.READ_CO2)
        response = self._read_response()
        if response[0] != 0xff or response[1] != 0x86:
            raise ValueError("Invalid response")
        elif response[8] != self._checksum(response[:8]):
            raise ValueError("Invalid checksum")

        return response[2] * 256 + response[3], response[4] - 40, response[5], response[6]

    def zero_calibration(self):
        """
        Zero calibration.
        """
        self._write_command(self.ZERO_CALIBRATION)

    def span_calibration(self, span: int):
        """
        Span calibration.
        """
        command = self.SPAN_CALIBRATION.copy()
        command[3] = span // 256
        command[4] = span % 256
        self._write_command(command)

    def set_auto_calibration(self, state: bool):
        """
        Set auto calibration point.
        """
        if state:
            self._write_command(self.AUTO_CALIBRATION)
        else:
            self._write_command(self.AUTO_CALIBRATION_OFF)

    def close(self):
        """
        Close serial port.
        """
        self.serial.close()
