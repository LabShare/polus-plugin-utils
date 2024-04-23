# Omero Download (v0.1.0-dev0)

This tool enables the retrieval of data from the Omero NCATS server.  [omero_plus](http://165.112.226.159/omero_plus/login/?url=%2Fwebclient%2F).

## Note
To access data from the Omero NCATS server, user must have to be connection to `NIHVPN`
1. Specify environmental variables for a server's username and password using the command prompt

   export `OMERO_USERNAME=XXXX` \
   export `OMERO_PASSWORD=XXXX`


Conda is employed to install all dependencies because one of the critical packages, `omero-py`, encountered installation issues with pip

Currently, the supported object types in a tool include:  `project`, `dataset`, `screen`, `plate`, `well`


## Building

To build the Docker image for the download plugin, run
`bash build-docker.sh`.

## Run the Docker image

To execute the built docker image for the download plugin, run
`bash run-plugin.sh`.

## Options

This plugin takes 2 input arguments and
1 output argument:

| Name            | Description                                                  | I/O    | Type        |
| --------------- | ------------------------------------------------------------ | ------ | ----------- |
| `--dataType`      | Object types to be retreived from Omero Server                    | Input  | String      |
| `--name  `      | Name of an object                   | Input  | String      |
| `--id  `      |  Identification of an object of an object                 | Input  | Integer      |
| `--outDir`      | Directory to store the downloaded data                  | Output | genericData |
| `--preview`      | Generate a JSON file with outputs                  | Output | JSON |



## Sample docker command:
```bash
docker run -e OMERO_USERNAME=$OMERO_USERNAME -e OMERO_PASSWORD=$OMERO_PASSWORD -v /home/ec2-user/data/:/home/ec2-user/data/ polusai/omero-download-tool:0.1.0-dev0 --dataType="plate" --id=108 --outDir=/home/ec2-user/data/output```