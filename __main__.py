from migratego2z import migratego2z
import argparse


def main():
    parser = argparse.ArgumentParser(prog='migratego2z')
    parser.add_argument('--domain', '-d', help='the target domain name',  nargs=1, default=[None])
    parser.add_argument('--rootDir', '-r', help='the root folder for e-mail import', dest='rootDir', nargs=1,
                        default=[None])
    parser.add_argument('--config', '-c', help='configuration file for import', nargs=1,
                        default=['/etc/migratego2z/migratego2z.ini'])
    args = parser.parse_args()
    prog = migratego2z.Main(args.rootDir[0], args.domain[0], args.config[0])
    prog.main()


if __name__ == "__main__":
    main()
