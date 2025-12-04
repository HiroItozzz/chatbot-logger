from cha2hatena.main import main
import sys

if __name__ == "__main__":
    try:
        exit_code = main()  # メイン処理

        print("アプリケーションは正常に終了しました。")
        sys.exit(exit_code)

    except Exception as e:
        print(
            "エラーが発生しました。\n実行を終了します。",
            exc_info=True,
        )
        sys.exit(1)
