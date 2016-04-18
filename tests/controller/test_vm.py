#!/usr/bin/env python
#
# Copyright (C) 2016 GNS3 Technologies Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest
import uuid
import asyncio
from unittest.mock import MagicMock


from tests.utils import AsyncioMagicMock

from gns3server.controller.vm import VM
from gns3server.controller.project import Project


@pytest.fixture
def compute():
    s = AsyncioMagicMock()
    s.id = "http://test.com:42"
    return s


@pytest.fixture
def vm(compute):
    project = Project(str(uuid.uuid4()))
    vm = VM(project, compute,
            name="demo",
            vm_id=str(uuid.uuid4()),
            vm_type="vpcs",
            console_type="vnc",
            properties={"startup_script": "echo test"})
    return vm


def test_json(vm, compute):
    assert vm.__json__() == {
        "compute_id": compute.id,
        "project_id": vm.project.id,
        "vm_id": vm.id,
        "vm_type": vm.vm_type,
        "name": "demo",
        "console": vm.console,
        "console_type": vm.console_type,
        "properties": vm.properties
    }


def test_init_without_uuid(project, compute):
    vm = VM(project, compute,
            vm_type="vpcs",
            console_type="vnc")
    assert vm.id is not None


def test_create(vm, compute, project, async_run):
    vm._console = 2048

    response = MagicMock()
    response.json = {"console": 2048}
    compute.post = AsyncioMagicMock(return_value=response)

    async_run(vm.create())
    data = {
        "console": 2048,
        "console_type": "vnc",
        "vm_id": vm.id,
        "startup_script": "echo test",
        "name": "demo"
    }
    compute.post.assert_called_with("/projects/{}/vpcs/vms".format(vm.project.id), data=data)
    assert vm._console == 2048
    assert vm._properties == {"startup_script": "echo test"}


def test_start(vm, compute, project, async_run):

    compute.post = AsyncioMagicMock()

    async_run(vm.start())
    compute.post.assert_called_with("/projects/{}/vpcs/vms/{}/start".format(vm.project.id, vm.id))


def test_stop(vm, compute, project, async_run):

    compute.post = AsyncioMagicMock()

    async_run(vm.stop())
    compute.post.assert_called_with("/projects/{}/vpcs/vms/{}/stop".format(vm.project.id, vm.id))


def test_suspend(vm, compute, project, async_run):

    compute.post = AsyncioMagicMock()

    async_run(vm.suspend())
    compute.post.assert_called_with("/projects/{}/vpcs/vms/{}/suspend".format(vm.project.id, vm.id))


def test_reload(vm, compute, project, async_run):

    compute.post = AsyncioMagicMock()

    async_run(vm.reload())
    compute.post.assert_called_with("/projects/{}/vpcs/vms/{}/reload".format(vm.project.id, vm.id))


def test_create_without_console(vm, compute, project, async_run):
    """
    None properties should be send. Because it can mean the emulator doesn"t support it
    """

    response = MagicMock()
    response.json = {"console": 2048, "test_value": "success"}
    compute.post = AsyncioMagicMock(return_value=response)

    async_run(vm.create())
    data = {
        "console_type": "vnc",
        "vm_id": vm.id,
        "startup_script": "echo test",
        "name": "demo"
    }
    compute.post.assert_called_with("/projects/{}/vpcs/vms".format(vm.project.id), data=data)
    assert vm._console == 2048
    assert vm._properties == {"test_value": "success", "startup_script": "echo test"}


def test_post(vm, compute, async_run):
    async_run(vm.post("/test", {"a": "b"}))
    compute.post.assert_called_with("/projects/{}/vpcs/vms/{}/test".format(vm.project.id, vm.id), data={"a": "b"})


def test_delete(vm, compute, async_run):
    async_run(vm.delete("/test"))
    compute.delete.assert_called_with("/projects/{}/vpcs/vms/{}/test".format(vm.project.id, vm.id))