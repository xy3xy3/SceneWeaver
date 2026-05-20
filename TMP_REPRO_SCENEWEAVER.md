# SceneWeaver 复现命令速查

这份文档按你当前机器路径整理，目标是：

- 单独创建两个 conda 环境
- 单独放一套 Blender 3.6，不和系统 `Blender 5.1.0` 冲突
- 配好 LLM API
- 给出前台和后台两种运行方式

默认项目路径：

```bash
cd /home/xy3/ht/SceneWeaver
```

## 1. 创建 conda 环境

先确保 conda 可用：

```bash
source ~/anaconda3/etc/profile.d/conda.sh
```

### 1.1 planner 环境：`sceneweaver`

```bash
cd /home/xy3/ht/SceneWeaver
conda env create -n sceneweaver -f environment_sceneweaver.yml
```

验证：

```bash
conda activate sceneweaver
python -V
python -c "import openai; print(openai.__version__)"
conda deactivate
```

### 1.2 executor 环境：`infinigen_python`

项目里的 `run/*.sh` 和 `run.sh` 默认用的是 `infinigen_python` 这个名字，所以直接照这个名字建最省事。

```bash
cd /home/xy3/ht/SceneWeaver
conda env create -n infinigen_python -f environment.yml
```

验证：

```bash
conda activate infinigen_python
python -V
python -c "import infinigen; print(infinigen.__version__)"
conda deactivate
```

## 2. 单独安装 Blender 3.6

你的系统里现在是：

```bash
blender -v
```

输出是 `Blender 5.1.0`。这个项目不要直接混用系统 Blender。

下面把 Blender 3.6 单独装到项目本地目录：

```bash
mkdir -p /home/xy3/ht/SceneWeaver/.local
cd /home/xy3/ht/SceneWeaver/.local
wget -O blender-3.6.0-linux-x64.tar.xz https://download.blender.org/release/Blender3.6/blender-3.6.0-linux-x64.tar.xz
tar -xf blender-3.6.0-linux-x64.tar.xz
mv blender-3.6.0-linux-x64 blender-3.6
rm blender-3.6.0-linux-x64.tar.xz
```

验证：

```bash
/home/xy3/ht/SceneWeaver/.local/blender-3.6/blender -v
```

你应该看到 `Blender 3.6.0`。

### 2.1 可选：给本项目单独加一个别名

这样不会覆盖系统 `blender`：

```bash
alias sw_blender=/home/xy3/ht/SceneWeaver/.local/blender-3.6/blender
sw_blender -v
```

## 3. 安装项目到 Blender 3.6 的 Python

这一步是为了让本地 Blender 3.6 能 import 项目代码。

```bash
cd /home/xy3/ht/SceneWeaver
/home/xy3/ht/SceneWeaver/.local/blender-3.6/3.6/python/bin/python3.10 -m ensurepip
CFLAGS="-I/usr/include/python3.10 -I/usr/include/ -I/usr/include/x86_64-linux-gnu" \
/home/xy3/ht/SceneWeaver/.local/blender-3.6/3.6/python/bin/python3.10 -m pip install -e .
```

如果这里报 `Python.h: No such file or directory`，先装系统的 Python 开发头文件再重试：

```bash
sudo apt update
sudo apt install -y build-essential python3.10-dev
```

如果上面失败，也可以直接使用项目自带脚本，但它默认会在当前目录生成 `blender/` 文件夹：

```bash
cd /home/xy3/ht/SceneWeaver
bash scripts/install/interactive_blender.sh
```

如果你已经按本文件前面的方式手动装好了 `.local/blender-3.6`，优先用手动方式，不必再跑这个脚本。

## 4. 配置 LLM API

这个项目现在主要依赖两个文件：

- `Pipeline/config/config.json`
- `Pipeline/key.txt`

### 4.1 写入 key

```bash
cat > /home/xy3/ht/SceneWeaver/Pipeline/key.txt <<'EOF'
YOUR_API_KEY
EOF
```

### 4.2 检查或修改 `Pipeline/config/config.json`

当前文件位置：

`/home/xy3/ht/SceneWeaver/Pipeline/config/config.json`

推荐内容如下：

```json
{
  "llm": {
    "api_type": "azure",
    "model": "gpt-4.1-2025-04-14",
    "base_url": "https://your-endpoint.openai.azure.com/openai/deployments/your-deployment",
    "api_key": "key.txt",
    "max_tokens": 8096,
    "temperature": 0.3,
    "api_version": "2025-03-01-preview"
  }
}
```

注意：

- 这个仓库的 `Pipeline/app/llm.py` 实际会从 `Pipeline/config/config.json` 读取 `api_key` 路径，再去打开 `Pipeline/key.txt`
- 代码里虽然还有 `TongGPT.py` 的旧逻辑，但主 `Pipeline/main.py` 这条链路要优先保证 `Pipeline/config/config.json` 和 `Pipeline/key.txt` 正确

## 5. 运行前的目录准备

创建输出目录：

```bash
mkdir -p /home/xy3/ht/SceneWeaver/outputs_runs
```

## 6. 运行方式

项目有两种常用方式。

### 6.1 方式 A：后台运行 Blender

这是 README 里最直接的方式。

先开一个终端，运行：

```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate sceneweaver
cd /home/xy3/ht/SceneWeaver/Pipeline
python main.py \
  --prompt "Design me a bedroom." \
  --cnt 1 \
  --basedir /home/xy3/ht/SceneWeaver/outputs_runs/
```

说明：

- 这条命令会由 `sceneweaver` 侧调起执行器
- 输出会落在 `/home/xy3/ht/SceneWeaver/outputs_runs/`

### 6.2 方式 B：前台运行 Blender

这种方式更方便观察 Blender 里的过程，需要两个终端。

#### 终端 1：启动 Blender socket server

```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate infinigen_python
cd /home/xy3/ht/SceneWeaver
python -m infinigen.launch_blender \
  -m infinigen_examples.generate_indoors_vis \
  --save_dir debug/ \
  -- \
  --seed 0 \
  --task coarse \
  --output_folder outputs/indoors/coarse_expand_whole_nobedframe \
  -g fast_solve.gin overhead.gin studio.gin \
  -p compose_indoors.terrain_enabled=False
```

如果你希望明确使用项目本地 Blender 3.6，可以这样启动：

```bash
export PATH=/home/xy3/ht/SceneWeaver/.local/blender-3.6:$PATH
source ~/anaconda3/etc/profile.d/conda.sh
conda activate infinigen_python
cd /home/xy3/ht/SceneWeaver
python -m infinigen.launch_blender \
  -m infinigen_examples.generate_indoors_vis \
  --save_dir debug/ \
  -- \
  --seed 0 \
  --task coarse \
  --output_folder outputs/indoors/coarse_expand_whole_nobedframe \
  -g fast_solve.gin overhead.gin studio.gin \
  -p compose_indoors.terrain_enabled=False
```

#### 终端 2：启动 agent

```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate sceneweaver
cd /home/xy3/ht/SceneWeaver/Pipeline
python main.py \
  --prompt "Design me a bedroom." \
  --cnt 1 \
  --basedir /home/xy3/ht/SceneWeaver/outputs_runs/ \
  --socket True
```

## 7. 最小自检命令

先分别测两个环境：

```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate sceneweaver
python -c "from openai import AzureOpenAI; print('sceneweaver ok')"
conda deactivate
```

```bash
source ~/anaconda3/etc/profile.d/conda.sh
conda activate infinigen_python
python -c "import infinigen; print('infinigen ok:', infinigen.__version__)"
conda deactivate
```

再测本地 Blender 和它自带的 `bpy`：

```bash
/home/xy3/ht/SceneWeaver/.local/blender-3.6/blender -v
/home/xy3/ht/SceneWeaver/.local/blender-3.6/3.6/python/bin/python3.10 -c "import bpy; print('bpy ok:', bpy.app.version_string)"
```

## 8. 已知坑

- 不要把系统 `Blender 5.1.0` 和项目要求的官方 Blender 3.6 运行时混着当同一套运行时
- `Pipeline/config/config.json` 和 `Pipeline/key.txt` 要同时存在
- 仓库默认代码还引用了一些外部数据集路径；如果你要完整跑 `init_physcene` / `init_metascene`，后面还要补数据资源
- 如果只是先验证主流程跑通，优先从 `init_gpt` 路线开始

## 9. 一套最短启动顺序

```bash
source ~/anaconda3/etc/profile.d/conda.sh
cd /home/xy3/ht/SceneWeaver
conda activate sceneweaver
cd Pipeline
python main.py --prompt "Design me a bedroom." --cnt 1 --basedir /home/xy3/ht/SceneWeaver/outputs_runs/
```

如果这一步报 Blender 或执行器相关错误，再切换到前台双终端方式排查。
