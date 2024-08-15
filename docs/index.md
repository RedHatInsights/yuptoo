# Overview
The Yuptoo service is responsible for processing bulk uploads of hosts.
A client(rh-cloud-plugin/satellite) will create a specially crafted tarball and send the file to the Insights Ingress service. The Ingress service will notify yuptoo via Kafka that a tarball has arrived for processing. Yuptoo downloads the tarball, performs top level validation, and sends the host JSON to the Insight's Host Inventory service.

[Code Repository](https://github.com/RedHatInsights/yuptoo)

## Architectural Diagram
![Yuptoo Arch diagram](./images/yuptoo.png)

## How It Works
The following sequence diagram shows the data flow and processing of payload recevied on `platform.upload.announce` kafka topic.

![Sequence Diagram](./images/sequence_diagram.png)
