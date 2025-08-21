import readline
import traceback

from calc import BinaryCalculator, BinCalcException


def main():
    calculator = BinaryCalculator()

    while True:
        idn = calculator.get_id()

        try:
            line = input(f"[{idn}] ")
            if not line:
                print()
                continue

            v = calculator.eval(line)
            print(v)
            print()

        except BinCalcException as e:
            print(e)
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
        except EOFError:
            break
        except Exception as e:
            print("internal error")
            traceback.print_exception(e)


if __name__ == "__pytool__":
    main()

