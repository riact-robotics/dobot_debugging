import time
import numpy as np
from TCP_IP_Python_V4.dobot_api import DobotApiDashMove, MyType


class ReadAtRate(DobotApiDashMove):
    def __init__(self, ip, portDash=29999, portFeed=30004, rate=125, *args):
        self.rate = rate
        self.is_dead = False

        super().__init__(ip, portDash=portDash, portFeed=portFeed, *args)

    def recvFeedData(self):
        total_read = 0
        start_time = time.perf_counter()
        time_per_read = 1 / self.rate
        little_endian_test_value = (0x0123456789abcdef).to_bytes(length=8, byteorder='little')

        try:
            hasRead = 0
            while True:
                data = bytes()
                while hasRead < 1440:
                    try:
                        temp = self.socket_dobot_feed.recv(1440 - hasRead)
                        if len(temp) > 0:
                            hasRead += len(temp)
                            data += temp
                    except Exception as e:
                        print(e)
                        self.socket_dobot_feed = self.reConnect(
                            self.ip, self.portFeed)

                hasRead = 0

                assert data[48:48+8] == little_endian_test_value, f"Expected data: {little_endian_test_value.hex()}, got {data[48:48+8].hex()}"
                total_read += 1

                with self._DobotApiDashMove__Lock:
                    self._DobotApiDashMove__MyType = []
                    self._DobotApiDashMove__MyType = np.frombuffer(data, dtype=MyType)

                # Sleep to maintain rate
                time.sleep(max(start_time + total_read * time_per_read - time.perf_counter(), 0))
                if total_read % 10 == 0:
                    print(f'Read: {total_read}')
        except Exception as e:
            print(f"Exception raised after {total_read} messages after {time.perf_counter() - start_time} seconds")
            print(f"Test value existed in data at index: {data.find(little_endian_test_value)}")
            print(f"Error was: {repr(e)}")
            self.is_dead = True


def main():
    """
    CR20a:

    | Rate | Seconds to assertion error | Messages read until error |
    | ---- | -------------------------- | ------------------------- |
    | 1    | 80                         | 80                        |
    | 20   | 4.7                        | 94                        |
    | 50   | 2.6                        | 131                       |
    | 110  | 7.8                        | 864                       |
    | 120  | 70-90                      | 9000-10000                |


    CR10a:

    | Rate | Seconds to assertion error | Messages read until error |
    | ---- | -------------------------- | ------------------------- |
    | 50   | 130                        | 6526                      |
    | 115  | 696                        | 80060                     |
    """

    dashboard = ReadAtRate('192.168.2.3', rate=1)

    while not dashboard.is_dead:
        pass


if __name__ == '__main__':
    main()
