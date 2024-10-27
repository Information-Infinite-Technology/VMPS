from vmps.task import VMPSTask
import yaml
with open("example/config.yaml") as f:
    config = yaml.safe_load(f)
task = VMPSTask(config)
task.process()
