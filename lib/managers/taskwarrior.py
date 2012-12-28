#!/usr/bin/env python
# vim: set sw=4 sts=4 et foldmethod=indent :

"""A manager to execute custom commands"""

from subprocess import check_output, call
import json

DEFAULT_FILTERS = []
# Add a default filter to taskwarrior. This is the same one you would use on
# the command line with the task executable.
# TODO: This should be moved in a configuration variable of some sort in the
# gui
# DEFAULT_FILTERS = ['+today']

class Taskwarrior:
    """A manager to execute custom commands"""
    def __init__(self):
        pass

    # Sadly we have to get all tasks for this each time as there might be calls
    # to taskwarrior that are changing the ids id.not=0 will give us only the
    # not completed tasks
    #TODO: we should check the taskwarrior team for the proper
    # way to do this. I am not sure if id.not=0 is a documented standard way for doing this.
    def __get_current_tasks(self, task_filters = ['id.not=0']):
        assert isinstance(task_filters, list)
        # use the default platform encoding (for portability reasons)
        command = ['task'] + DEFAULT_FILTERS + task_filters + ['export']
        exported_data = check_output(command).decode()
        return json.loads('[' + exported_data + ']')


    def task_count(self):
        return len(self.__get_current_tasks())

    def get_task(self, i):
        task = self.__get_current_tasks()[i]
        # pomodoros is a user defined attribute we are looking for
        due = task['due'] if 'due' in task else -1
        pomodoros = task['pomodoros'] if 'pomodoro' in task else -1
        return (task['id'], task['description'], due, pomodoros)

    def start_task(self, task_id):
        task = self.__get_current_tasks([str(task_id)])[0]
        return call(['task', str(task['id']), 'start'])


    def complete_task(self, task_id):
        # No proper implementation for now
        return False
