## M.W
M.Wは Discord Botです。 [R](https://github.com/mirielnet/R)の後継BOTです。

### 必要要件
Python 3.9.18以降
pip 21.2.3以降
FFMPEGが必要です。

### 起動マニュアル
本BOTはPython仮想環境 で動作します。

    python3 -m venv venv
    source venv/bin/activate (Linux)
    venv\Scripts\activate (Windows)
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8000

### ライセンスについて
本BOT(リポジトリ)は、[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.ja) を採用しております。
ですので、Forkなどをする際にはこれを厳守しForkしていただきますようよろしくお願いいたします。

-   **Attribution (著作権表示)**: 作品の作者を明記する必要があります。
-   **Non-Commercial (非営利)**: 作品を商業目的で利用することはできません。
-   **ShareAlike (継承)**: 新たに作成した作品も同じライセンス(CC BY-NC-SA 4.0)で公開しなければなりません。

