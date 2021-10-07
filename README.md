# Start 
### Pre-request 
- must install pipenv
- must install docker.
### Folder structure
- mininet: mininet run on docker container.
- controller: ryu controller run on host.

---

## Start mininet
- start ryu before start mininet
```
make mininet-start
<docker container> python3 /mininet/normal.py $(dig host.docker.internal +short) 
<docker container> python3 /mininet/attack.py $(dig host.docker.internal +short) 
```
---
## Start Ryu
- start ryu before start mininet
```
# detect DDoS
make controller-detect
# collect traffic
make controller-collect
```
---
