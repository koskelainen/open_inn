## Conda env

Project working with Conda venv.

```bash
conda create -n open_inn python=3.10 
conda activate open_inn
```

<details>
<summary>
Create anaconda venv with details
</summary>

if you have pip file: `requirements.txt`
```shell
$ conda install --file requirements.txt # install libs
```

if you have conda file: `environment.yml`
```shell
$ conda env create -f environment.yml # create environments
$ conda env update -n <your_env_name> --file environment.yml # update/install libs
```
manual command to create environments
```shell
$ conda create -n <your_env_name> python=3.10 notebook pandas 
```

</details>

## Install system dependencies

Update system dependents and install libs for cv2

```bash
sudo apt-get update && sudo apt-get install ffmpeg libsm6 libxext6  -y
```


## Prepare postgresql database

Install postgresql
```bash
sudo apt install postgresql
```

Then enter to postgres database

```bash
sudo -u postgres psql
```
apply sql snippet `sql/prepare_database.sql`

Make `.env` file from the example. It will used for work with database:

```bash
cp .env_example .env
vim .env
```

After that run `upload.py` script:

```bash
python src/app/upload.py -w 150 -f <path_to_csv_file>
```

## Run server Fast API

DEV environment

```bash
uvicorn main:app --reload
```
PROD environment

```bash
uvicorn main:app --workers 2 --host 0.0.0.0 --port 80
```

## Request test

DEV environment with `curl`

```bash
curl -X 'GET' -H 'accept: application/json' 'http://127.0.0.1:8000/image/?depth_min=9000.1&depth_max=9001.7'
```
DEV environment with `httpie`

```bash
http --json POST http://127.0.0.1:8000/image/ depth_min=9000.1 depth_max=9001.7
http --json POST http://127.0.0.1:8000/image/ depth_min=9000.1 depth_max=9001.7 colormap=2
```

PROD environment with `curl`

```bash
curl -X 'GET' -H 'accept: application/json' \
 'http://<remote_host>/image/?depth_min=9050.1&depth_max=9051.7'

curl -X 'GET' -H 'accept: application/json' \
 'http://<remote_host>/image/?depth_min=9000.1&depth_max=9000.7&colormap=2'
```
PROD environment with `httpie`

```bash
http --json POST http://<remote_host>/image/ depth_min=9000.1 depth_max=9001.7
http --json POST http://<remote_host>/image/ depth_min=9000.1 depth_max=9001.7 colormap=2
```

## Deploy src to remote server

Copy src files from localhost to `remote_host` by `rcp`
All project files:

```bash
scp -r ./ <user_name>@<remote_host>:/<root_project_path>
```

Only target files

```bash
scp -r ./src/*.py <user_name>@<remote_host>:/<root_project_path>/src
```