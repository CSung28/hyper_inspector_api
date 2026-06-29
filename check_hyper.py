from tableauhyperapi import HyperProcess, Telemetry

print("tableauhyperapi import success")

with HyperProcess(
    telemetry=Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU,
    user_agent="hyper-inspector-api",
) as hyper:
    print("HyperProcess started")
    print(hyper.endpoint)
