# Phira v0.9.0 — 噪域（`blockAreaList`）支持

> 基于 `TeamFlos/phira` main（`ac4795f`）构建。对应 PR：https://github.com/TeamFlos/phira/pull/901

## 新增：支持 Phigros「噪域」（`blockAreaList`）

Phigros 4.0.0 起，谱面新增了顶层字段 `blockAreaList`（玩家俗称「噪域 / 红区」）。
在此之前 Phira 的谱面解析器里没有这个字段，属于**静默丢弃**：谱面能正常打开、音符照常下落，
但红区的显示与判定影响全部缺失。从 v0.9.0 起，Phira 完整支持该字段。

### 判定

- 手指落在生效中的噪域内时，**该手指完全不参与判定**：点击、滑动、接黄键、长按都不生效。
- 手指从噪域内移动到噪域外**不松手**，依然不生效——被挡住的手指要抬起才会解除。
- 减算方块（`isSubtract`）按并集异或参与遮挡计算。区域最外一圈容差带不计入遮挡，
  边界本身不会产生抖动式判定。
- **键盘游玩同样受限**：开启「使用键盘游玩」时，键盘按键不带坐标，原先会直接判掉全谱最早
  一个未判音符，从而绕开噪域。现在改为在判定音符的那一刻检查该音符是否落在生效中的噪域内，
  被盖住的音符键盘也打不到；按住按键让 Drag / Flick 全屏预判的那条路径同样受限。
- 自动演奏（Autoplay）不受影响。

### 显示

- 渲染管线直接移植自原版素材：位移、噪波、边缘光、触碰红光的 GLES2 着色器与贴图，
  不再是近似实现。
- 完整还原 5 个阶段：`HiddenBefore` → `Disabled` → `Ready` → `Active` → `HiddenAfter`。
  其中 `Disabled` 到 `Ready` 的 0.5 秒渐显、`Ready` 的 0.5 秒预备时长，均与原版预制件常量一致。
- 位置、旋转、缩放、移动事件按谱面时间插值；缓动曲线使用原版的
  `n = (type - 1) / 3 + 2` 幂函数与 101 项查表 + 线性插值，而不是常见的正弦/二次缓动。
- 手指压在噪域上时，对应位置出现红光特效。

### 新增设置项

| 键 | 默认 | 说明 |
|:--|:--|:--|
| `noise_area.enabled` | `true` | 噪域总开关；谱面不含 `blockAreaList` 时完全不受影响 |
| `noise_area.low_performance` | `false` | 使用简化渲染路径（不创建离屏目标、不编译着色器） |
| `noise_area.remove_distortion` | `false` | 关闭位移扭曲，保留其余画面表现 |
| `noise_area.no_jitter` | `false` | 噪域不抖动：冻结随时间变化的位移与 SDF 噪声，边缘保持静止 |
| `noise_area.precise_edges` | `false` | 边缘覆盖采样（更准，开销更高） |
| `noise_area.music_unaffected` | `false` | 保留项：不随噪域触碰改音乐 |

其中 `noise_area.no_jitter`（**设置 → 谱面 → 噪域不抖动**）可在游戏内随时切换，改完立刻生效，
不需要重进谱面。选中 `NO_SHADER` Mod 时会自动回退到简化渲染路径。

## 其他

- 版本号提升至 `0.9.0`。
- 15 种语言的 locale 均已补上 `item-noise-no-jitter`。

## 产物说明

| 文件 | 平台 | 说明 |
|:--|:--|:--|
| `Phira-windows-x86_64-v0.9.0.zip` | Windows x86_64 | 解压后运行 `phira-main.exe` |
| `Phira-windows-aarch64-v0.9.0.zip` | Windows on ARM | 解压后运行 `phira-main.exe` |
| `Phira-linux-x86_64-v0.9.0.zip` | Linux x86_64 | 解压后运行 `phira-main` |
| `Phira-android-arm64-v8a-v0.9.0.apk` | Android arm64-v8a | 可直接安装，**需先卸载官方版**（签名不同） |
| `Phira-android-armeabi-v7a-v0.9.0.apk` | Android armeabi-v7a | 同上 |

> ⚠️ Android 包是**拿官方 APK 换掉 `lib/<abi>/libphira.so` 后重新签名**得到的。
> `TeamFlos/phira` 仓库里没有 Android 前端工程（无 gradle / manifest / Java 源码），
> 官方 APK 是唯一可用的宿主外壳，这也正是官方构建文档《Android》给出的做法。
> 因此有几点要注意：
> - 用的是我们自己的证书：**包名与官方相同、签名不同**，安装前必须先卸载官方版。
> - APK 内的版本信息仍是上游的 `0.8.2 (39)`，只有 `libphira.so` 换成了本次的 v0.9.0 构建。
> - 换上去的 so 补齐了宿主所需的全部 `quad_native.QuadNative` JNI 符号。
>
> ⚠️ 本版本**未提供 HMOS（OpenHarmony）产物**。构建 HMOS 需要华为 DevEco Studio / HarmonyOS
> Command Line Tools（NDK ≥ API 20）与 `phira-ohos` 前端工程，不在本次构建环境内。

## 已知差异

- Android 包替换进官方 APK 的 `libphira.so` 里，`quad_native.QuadNative.preprocessInput`
  是空实现。开源构建与官方 APK 的 so 符号差异只有这一个（其余 26 个均一致），而它不参与
  触摸/按键主通路——宿主真正调的是 `surfaceOnTouch` / `surfaceOnKey*`，所以留空不影响操作。
  上游若日后开源 Android 前端，这个空实现即可删除。
- 原版在「有手指被噪域挡住」时会对音乐做低通模糊（`cutoff` 1500Hz 渐变到 22000Hz）。
  这需要改动音频后端 `sasa`，本次未实现，`music_unaffected` 开关暂为占位。
- 噪域的着色器与贴图取自原版游戏资源，与 Phigros 官方素材一致。
