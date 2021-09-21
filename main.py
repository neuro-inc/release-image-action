#! /usr/bin/env python3

import json
import os
import re
import subprocess
import sys

ctx = json.loads(os.environ["INPUT_GITHUB"])
event_name = ctx["event_name"]
if event_name != "workflow_run":
    print(
        f"::error::Invalid event type {event_name}, "
        "release-image-action should be executed on 'workflow_run' event"
    )
    sys.exit(1)

token = os.environ["INPUT_TOKEN"]
image = os.environ["INPUT_IMAGE"]
artifact = os.environ["INPUT_ARTIFACT"]

sha = ctx["sha"]

actor = ctx["actor"]

repo = ctx["repository"]

owner = ctx["repository_owner"]

default_branch = ctx["event"]["repository"]["default_branch"]

workflow_run = ctx["event"]["workflow_run"]
default_ref = "refs/heads/" + default_branch
skip = ctx["ref"] != default_ref
if not skip:
    skip = workflow_run["event"] != "push"
if not skip:
    skip = workflow_run["head_branch"] == default_branch
if not skip:
    skip = workflow_run["conclusion"] != "success"


def dump(val):
    if val:
        return "Y"
    else:
        return ""


head_branch = ctx["event"]["workflow_run"]["head_branch"]
if not skip:
    match = re.match(r"^v\d+\.\d+(\.\d+)?(?P<pre>(a|b|rc)\d*)?$", head_branch)
    if not match:
        print(
            f"::error:: Invalid tag {head_branch}; ",
            "The tag should have vYY.MM[.NN][{a|b|rc}N] format ",
            "where YY is the current year, MM is the current month, "
            "NN is incremental number, "
            "every next month resets the number to 0, "
            "a -- alpha, b -- beta, rc -- release candidate, N -- number.",
        )
        sys.exit(1)
    else:
        print(f"::set-output name=tag::{head_branch}")
        version = head_branch[1:]
        print(f"::set-output name=version::{version}")
        print(f"::set-output name=prerelease::{dump(match.group('pre'))}")


run_id = workflow_run["id"]
print(f"::notice::Run id: {run_id}")

print(f"::set-output name=skip::{dump(skip)}")

if skip:
    print("::notice::Skip release")
    sys.exit(0)

print(f"::notice::download artifact {artifact}")
subprocess.run(
    ["gh", "run", "download", str(run_id), "--name", artifact, "--repo", repo],
    check=True,
    env={"GITHUB_TOKEN": token},
)

print("::notice::login to docker")
subprocess.run(
    ["docker", "login", "-u", actor, "--password-stdin", "ghcr.io"],
    input=token.encode("utf8"),
    check=True,
)

print(f"::notice::load imge {image} into docker")
subprocess.run(["docker", "load", "--input", f"{image}.tar"], check=True)

print("::notice::tag remote image")
subprocess.run(
    ["docker", "tag", f"{image}:latest", f"ghcr.io/{owner}/{image}:latest"],
    check=True,
)
subprocess.run(
    ["docker", "tag", f"{image}:latest", f"ghcr.io/{owner}/{image}:{version}"],
    check=True,
)

print("::notice::push to ghcr.io")
subprocess.run(
    ["docker", "push", f"ghcr.io/{owner}/{image}:latest"],
    check=True,
)
subprocess.run(
    ["docker", "push", f"ghcr.io/{owner}/{image}:{version}"],
    check=True,
)
