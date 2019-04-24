import subprocess
import re
from json import loads
from urllib.error import HTTPError
from urllib.request import urlopen
import argparse
import sys
import time

started_message = 'Трассировка маршрута к'

def check_start(msg1, msg2):
    if msg2.find(started_message) == -1:
        print('Incorrect input: ' + msg1)
        exit(1)

def tracert_get_ips(args): # args - list of strings
    tracert = subprocess.Popen(args = get_new_args(args), stdout= subprocess.PIPE, stdin=subprocess.PIPE)
    num = 1
    start_msg1 = tracert.stdout.readline().decode('cp866')
    start_msg2 = tracert.stdout.readline().decode('cp866')
    check_start(start_msg1, start_msg2)
    print(start_msg2)
    while True:
        output = tracert.stdout.readline().decode('cp1251').strip()
        if tracert.poll() is not None:
            break
        if output:
            stars = check_for_stars(output)
            if len(stars) == 3:
                yield 'Превышен интервал ожидания для запроса.'
                break
            ip = parse_output(output)
            if len(ip) == 0:
                continue
            data = get_ip_info(ip[0])
            yield str(num) + ' \ ' + data['ip'] + ' \ ' + data['country'] + ' \ ' + data['org']
            num += 1

def check_for_stars(data):
    #  14     *        *        *     Превышен интервал ожидания для запроса.
    r = re.compile('\*')
    return re.findall(r, data)

def get_new_args(args):
    new_args = list()
    new_args.append("tracert")
    if args is not None:
        for i in args:
            new_args.append(i)
    return new_args

def parse_output(data):
    r = re.compile('(?:[0-9]{1,3}\\.){3}[0-9]{1,3}')
    return re.findall(r, data)

def get_ip_info(ip):
    try:
        return get_response(ip)
    except HTTPError:
        time.sleep(5)
        return get_response(ip)

def get_response(ip):
    response = loads(urlopen('https://ipinfo.io/{}/json'.format(ip)).read())
    if response.get('bogon') == True:
        d = dict()
        d['ip'] = ip
        d['country'] = 'None'
        d['org'] = 'local'
        return d
    return response

def main():
    parser = argparse.ArgumentParser(description= 'AS information')
    parser.add_argument('-a', '--address', required=True, action='store')
    args = sys.argv
    args.pop(0)
    parsed_args = parser.parse_args(args)
    l = list()
    l.append(parsed_args.address)

    for line in tracert_get_ips(l):
        print(line)
    print('Done')

if __name__ =='__main__':
    main()