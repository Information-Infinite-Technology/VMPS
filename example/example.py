from vmps.task import VMPSTask
import yaml
with open("test/test1.yaml") as f:
    config = yaml.safe_load(f)
task = VMPSTask("test", config)
task.process()
