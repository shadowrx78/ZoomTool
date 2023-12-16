# ZoomTool

一个简单的放大镜工具

图标在通知栏里

![image](https://github.com/shadowrx78/ZoomTool/blob/main/image/temp.png)

锁定后效果如下：

![image](https://github.com/shadowrx78/ZoomTool/blob/main/image/example.gif)

## PyInstaller打包命令：

```
py -3 -m PyInstaller ZoomTool.py -F --add-data .\icon;.\icon --onefile --windowed --icon=.\icon\icon.ico -w
```