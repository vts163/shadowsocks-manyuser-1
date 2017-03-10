#!/usr/bin/python
# -*- coding: UTF-8 -*-

import logging
import cymysql
import time
import sys
import socket
import config
import json
import urllib2, urllib


class DbTransfer(object):
    instance = None

    def __init__(self):
        self.last_get_transfer = {}

    @staticmethod
    def get_instance():
        if DbTransfer.instance is None:
            DbTransfer.instance = DbTransfer()
        return DbTransfer.instance

    @staticmethod
    def get_mysql_config():
        return {
            'host': config.MYSQL_HOST,
            'port': config.MYSQL_PORT,
            'user': config.MYSQL_USER,
            'passwd': config.MYSQL_PASS,
            'db': config.MYSQL_DB,
            'charset': 'utf8'
        }

    @staticmethod
    def send_command(cmd):
        data = ''
        try:
            cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            cli.settimeout(1)
            cli.sendto(cmd, ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
            data, addr = cli.recvfrom(1500)
            cli.close()
            # TODO: bad way solve timed out
            time.sleep(0.05)
        except:
            logging.warn('send_command response')
        return data

    @staticmethod
    def get_servers_transfer():
        dt_transfer = {}
        cli = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        cli.settimeout(2)
        cli.sendto('transfer: {}', ('%s' % (config.MANAGE_BIND_IP), config.MANAGE_PORT))
        bflag = False
        while True:
            data, addr = cli.recvfrom(1500)
            if data == 'e':
                break
            data = json.loads(data)
            # print data
            dt_transfer.update(data)
        cli.close()
        return dt_transfer

    @staticmethod
    def push_db_all_user():
        dt_transfer = DbTransfer.get_instance().get_servers_transfer()
        conn = cymysql.connect(**DbTransfer.get_instance().get_mysql_config())
        cursor = conn.cursor()

        sql = 'SELECT user_id, port from ss_user'
        cursor.execute(sql)
        port_to_user = {}
        for item in cursor.fetchall():
            port_to_user[str(item[1])] = item[0]

        insert_rows = []
        sql = 'INSERT INTO ss_transfer (node_id, user_id, flow_up, flow_down) VALUES (%s, %s, %s, %s)'
        for id in dt_transfer.keys():
            user_id = port_to_user[str(id)]
            insert_rows.append([config.NODE_ID, user_id, 0, dt_transfer[id]])
        cursor.executemany(sql, insert_rows)
        conn.commit()

        query_head = 'UPDATE ss_user'
        query_sub_when = ''
        query_sub_when2 = ''
        query_sub_in = None
        last_time = time.strftime('%Y-%m-%d %H:%M:%S')
        for id in dt_transfer.keys():
            query_sub_when += ' WHEN %s THEN flow_up+%s' % (id, 0)  # all in d
            query_sub_when2 += ' WHEN %s THEN flow_down+%s' % (id, dt_transfer[id])
            if query_sub_in is not None:
                query_sub_in += ',%s' % id
            else:
                query_sub_in = '%s' % id
        if query_sub_when == '':
            return
        sql = query_head + ' SET flow_up = CASE port' + query_sub_when + \
                    ' END, flow_down = CASE port' + query_sub_when2 + \
                    ' END, active_at = "%s"' % (last_time) + \
                    ' WHERE port IN (%s)' % query_sub_in
        # print sql
        cursor.execute(sql)
        cursor.close()
        conn.commit()

    @staticmethod
    def pull_db_all_user():
        conn = cymysql.connect(**DbTransfer.get_instance().get_mysql_config())
        cursor = conn.cursor()
        cursor.execute("SELECT port, flow_up, flow_down, transfer_enable, password, is_locked FROM ss_user")
        rows = []
        for r in cursor.fetchall():
            rows.append(list(r))
        cursor.close()
        conn.close()
        return rows

    @staticmethod
    def del_server_out_of_bound_safe(rows):
        for row in rows:
            server = json.loads(DbTransfer.get_instance().send_command('stat: {"server_port":%s}' % row[0]))
            if server['stat'] != 'ko':
                if row[5] == 'Y':
                    # stop disable or switch off user
                    logging.info('db stop server at port [%s] reason: disable' % (row[0]))
                    DbTransfer.send_command('remove: {"server_port":%s}' % row[0])
                elif row[1] + row[2] >= row[3]:
                    # stop out bandwidth user
                    logging.info('db stop server at port [%s] reason: out bandwidth' % (row[0]))
                    DbTransfer.send_command('remove: {"server_port":%s}' % row[0])
                if server['password'] != row[4]:
                    # password changed
                    logging.info('db stop server at port [%s] reason: password changed' % (row[0]))
                    DbTransfer.send_command('remove: {"server_port":%s}' % row[0])
            else:
                if row[5] == 'N' and row[1] + row[2] < row[3]:
                    logging.info('db start server at port [%s] pass [%s]' % (row[0], row[4]))
                    DbTransfer.send_command('add: {"server_port": %s, "password":"%s"}' % (row[0], row[4]))
                    # print('add: {"server_port": %s, "password":"%s"}'% (row[0], row[4]))

    @staticmethod
    def thread_db():
        import socket
        import time
        timeout = 30
        socket.setdefaulttimeout(timeout)
        while True:
            logging.info('db loop')
            try:
                rows = DbTransfer.get_instance().pull_db_all_user()
                DbTransfer.del_server_out_of_bound_safe(rows)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.warn('db thread except:%s' % e)
            finally:
                time.sleep(config.CHECKTIME)

    @staticmethod
    def thread_push():
        import socket
        import time
        timeout = 30
        socket.setdefaulttimeout(timeout)
        while True:
            logging.info('db loop2')
            try:
                DbTransfer.get_instance().push_db_all_user()
            except Exception as e:
                import traceback
                traceback.print_exc()
                logging.warn('db thread except:%s' % e)
            finally:
                time.sleep(config.SYNCTIME)
