"""
タイマー付レシピ

    手順に記載されたx分を強調表示し、それをクリックするとタイマーが起動
    料理のヒントに記載されたURLの文字色を変更し、それをクリックするとリンクをブラウザで表示
    instructions : 手順
    ingredients  : 材料
    cooking_tips : 料理のヒント(説明)
"""
from logging import getLogger, StreamHandler, Formatter
logger = getLogger(__name__)

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tkinter import font as tkf
from tkinter.scrolledtext import ScrolledText
import pandas as pd
import sys, os, pathlib, webbrowser
sys.path.append(os.path.dirname(sys.executable))    # 実行時フォルダをパスに追加
import settings_recipe as stgs

class MyFrame(tk.Frame):
    """
    ビュークラス
    """
    def __init__(self, master) -> None:
        """
        コンストラクタ：画面作成
        """
        super().__init__(master)

        # スタイルの初期化
        self.stl = ttk.Style()        # スタイルオブジェクト作成
        self.stl.theme_use('alt')     # 先にテーマを指定し、個別設定への上書きを抑制。
        # Treeviewで使われているフォントを取得(configure実施前でないと取れない)
        fontname = self.stl.lookup('Treeview', 'font')  # スタイルからTreeveiwのフォント名を取得
        self.tvfont = tkf.nametofont(fontname)          # フォント名からFontオブジェクトを作成
        # スタイルのフォント、フォントサイズを変更(ttkウィジェット)
        self.stl.configure(".", font=(stgs.FONT, stgs.FONT_SIZE))

        # mapメソッドでbackgroundを指定するとタグのbackgroundも機能するようになる
        self.stl.map("Treeview", background=[('selected', '#99998b')])	# 灰色

        # プログレスバーの作成
        self.cd = tk.IntVar(self, value=0)      # プログレスバー用カウントダウン値
        self.create_progressbar(master)         # プログレスバー作成

        # フレーム作成
        f_inss = tk.LabelFrame(master, text="手順")     # 手順フレーム
        f_ings = tk.LabelFrame(master, text="材料")     # 材料フレーム
        f_tips = tk.LabelFrame(master, text="説明")     # 料理のヒントフレーム
        f_tree = tk.Frame(master)                       # ツリービューフレーム
        f_btns = tk.Frame(f_tree)                       # ボタンフレーム

        # フレーム、プログレスバーの配置    ツリービューフレームを右に残りを上から
        f_tree.pack(side=tk.RIGHT, fill=tk.Y)
        f_inss.pack(fill=tk.BOTH, expand=True, anchor=tk.N)
        self.p_bar.pack(fill=tk.X, expand=False, anchor=tk.N)
        f_ings.pack(fill=tk.BOTH, expand=True, anchor=tk.N)
        f_tips.pack(fill=tk.BOTH, expand=True, anchor=tk.N)

        # 手順フレーム内
        self.t_inss = ScrolledText(f_inss, bg=stgs.BG_T_INSS, 
                                    fg=stgs.FG_T_INSS,
                                    height=stgs.HEIGHT_T_INSS, 
                                    width=stgs.TEXT_WIDTH)  # テキストウィジェットの作成
        self.t_inss.pack(fill=tk.BOTH, expand=True)
        self.t_inss.bind('<<Modified>>', self.on_text_change)

        # 材料フレーム内
        self.t_ings = ScrolledText(f_ings, bg=stgs.BG_T_INGS, 
                                    fg=stgs.FG_T_INGS,
                                    height=stgs.HEIGHT_T_INGS, 
                                    width=stgs.TEXT_WIDTH) # テキストウィジェットの作成
        self.t_ings.pack(fill=tk.BOTH, expand=True)
        self.t_ings.bind('<<Modified>>', self.on_text_change)

        # 説明フレーム内
        self.t_tips = ScrolledText(f_tips, bg=stgs.BG_T_TIPS, 
                                    fg=stgs.FG_T_TIPS,
                                    height=stgs.HEIGHT_T_TIPS, 
                                    width=stgs.TEXT_WIDTH)   # テキストウィジェットの作成
        self.t_tips.pack(fill=tk.BOTH, expand=True)
        self.t_tips.bind('<<Modified>>', self.on_text_change)

        # ツリービューフレーム内
        # ツリービュー
        self.tv = ttk.Treeview(f_tree, show="headings") # ツリービュー作成 料理名
        # ツリービューの行の高さをフォントに合わせて設定
        rowheight = self.tvfont.metrics('linespace')
        logger.debug(f'{rowheight=}')
        self.stl.configure('Treeview', rowheight=rowheight)
        # ツリービューの行のストライプ用タグ作成
        self.tv.tag_configure('oddrow', background='ivory2')
        # ツリービュー用スクロールバー作成
        sbar = tk.Scrollbar(f_tree, orient=tk.VERTICAL, command=self.tv.yview)
        self.tv.config(yscrollcommand=sbar.set)     # Treeviewに垂直スクロールバーを設定
        # 配置(スクロールバーを先に)
        f_btns.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.S)
        sbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tv.pack(fill=tk.Y, expand=True, anchor=tk.N)

        # ボタンフレーム内
        # ボタン類の作成と配置
        self.b_upd  = tk.Button(f_btns, text="更新", command=self.upd_item)
        self.b_add  = tk.Button(f_btns, text="追加", command=self.add_item)
        self.b_del  = tk.Button(f_btns, text="削除", command=self.del_item)
        self.b_save = tk.Button(f_btns, text="保存")
        self.b_chk  = tk.Button(f_btns, text=" アラーム確認 ", command=self.do_alarm)
        # pack
        self.b_upd.pack(fill=tk.X, padx=5, pady=(3, 0))
        self.b_add.pack(fill=tk.X, padx=5, pady=(3, 0))
        self.b_del.pack(fill=tk.X, padx=5, pady=(3, 0))
        self.b_save.pack(fill=tk.X, padx=5, pady=(3, 0))
        self.b_chk.pack(fill=tk.X, padx=5, pady=3)

        # タイマー用タグの設定
        self.tag_timer = "timer"
        self.t_inss.tag_config(self.tag_timer, background=stgs.BG_TAG_TIMER)
        self.t_inss.tag_bind(self.tag_timer, "<Button-1>", self.start_countdown)
        self.t_inss.tag_bind(self.tag_timer, "<Enter>", self.show_hand_cursor)
        self.t_inss.tag_bind(self.tag_timer, "<Leave>", self.hide_hand_cursor)

        # URL用タグの設定
        self.tag_url = "url"
        self.t_tips.tag_config(self.tag_url, foreground="blue")
        self.t_tips.tag_bind(self.tag_url, "<Button-1>", self.show_url)
        self.t_tips.tag_bind(self.tag_url, "<Enter>", self.show_hand_cursor)
        self.t_tips.tag_bind(self.tag_url, "<Leave>", self.hide_hand_cursor)

    def show_hand_cursor(self, event=None):
        """
        手形のカーソルを表示
        """
        if not event: return
        event.widget.config(cursor="hand2")

    def hide_hand_cursor(self, event=None):
        """
        手形のカーソルを非表示
        """
        if not event: return
        event.widget.config(cursor='')

    def on_text_change(self, event=None):
        """
        Text widgetが更新されていたら更新ボタンの表示を変更
        """
        if not event: return
        if not event.widget.edit_modified(): return  # テキストが変更されたか確認
        self.b_upd.config(text="更新(変更あり)")
        event.widget.edit_modified(False)  # フラグをリセット

    def create_progressbar(self, parent):
        """
        プログレスバーの作成

        Args:
            parent:   親ウィジェット
        """
        # プログレスバーのスタイルを派生して調整
        self.stl.configure("my_pbar.TProgressbar", 
                            background=stgs.BG_P_BAR, 
                            font=("", 20), anchor=tk.CENTER, text="⏰")
        # プログレスバーのスタイルにラベルを追加
        self.stl.layout('my_pbar.TProgressbar', 
             [
                ('my_pbar.TProgressbar.label', {'sticky': 'nswe'})
              ])
        # 派生したスタイルでプログレスバーウィジェットを作成(確定モード、水平)
        self.p_bar = ttk.Progressbar(parent, variable=self.cd, 
                                    style="my_pbar.TProgressbar")

    def insert_t_widget(self, widget:tk.Text, text:str):
        """
        テキストウィジェットに文字列を設定
        文字数によりテキストウィジェットの高さを変更

        Args:
            widget(Text):   Textオブジェクト
            text(str):      文字列
        """
        widget.delete(1.0, tk.END)      # 元の文字列を削除
        widget.insert(tk.END, text)     # 新しい文字列を設定
        widget.edit_modified(False)     # 更新フラグをオフ(ユーザー編集と判断しないように)
        # lc = widget.count(1.0, tk.END, 'displaylines')  # 行数を取得
        # widget.config(height=lc)        # テキストウィジェットの高さを指定

    def clear_t_widget(self):
        """
        Text widgetの文字列をクリア
        """
        self.t_inss.delete(1.0, tk.END)
        self.t_inss.edit_modified(False)     # 更新フラグをオフ(ユーザー編集と判断しないように)
        self.t_ings.delete(1.0, tk.END)
        self.t_ings.edit_modified(False)     # 更新フラグをオフ(ユーザー編集と判断しないように)
        self.t_tips.delete(1.0, tk.END)
        self.t_tips.edit_modified(False)     # 更新フラグをオフ(ユーザー編集と判断しないように)

    def set_my_ctr(self, my_ctr):
        """
        MyControlクラスの参照を設定

        Args:
            my_ctr(MyControl):  MyControlオブジェクト
        """
        self.my_ctr = my_ctr
        # my_ctrにあるメソッドをバインド
        self.b_save.config(command=self.my_ctr.save)            # 保存ボタン
        self.tv.bind('<<TreeviewSelect>>', self.tv_selected)    # ツリービューの選択

    def tv_selected(self, event=None):
        """
        Treeviewで行が選択された時、内容を画面に表示
        料理名を選択し、レシピを表示、更新ボタンをクリア
        """
        if not event: return
        # Treeviewの選択項目のiidから値を取得
        self.tv_sel = self.tv.set(self.tv.selection()[0], column='names')
        self.my_ctr.row_to_disp(self.tv_sel)    # DataFrameの行を画面表示(レシピ内容表示)
        self.search_time_set_tag()              # テキストにタグ付(タイマー)
        self.search_url_set_tag()               # テキストにタグ付(URL)
        self.reset_p_bar()                      # プログレスバーをリセット
        self.update_idletasks()
        self.b_upd.config(text='更新')          # 変更は無視したことの表示

    def reset_p_bar(self):
        """
        プログレスバー動作中に選択変更された場合を考慮して動作を停止。
        """
        try:
            logger.debug(f"{self.after_id=}")
            self.after_cancel(self.after_id)
        except AttributeError:
            pass
        self.p_bar.stop()
        self.cd.set(0)
        self.stl.configure("my_pbar.TProgressbar", text="⏰")

    def search_time_set_tag(self, first_index:str="1.0"):
        """
        テキストにタグ付
        作り方の内容の「～分」にタグを付ける

        Args:
            first_index(str):   検索開始位置
        """
        count = tk.IntVar(self, value=0)
        pos = self.t_inss.search("\d+分", first_index, tk.END, regexp=True, count=count)
        if not pos: return
        sel_end_pos = f"{pos}+{count.get()}c"
        self.t_inss.tag_add(self.tag_timer, pos, sel_end_pos)
        logger.debug(f"{self.t_inss.tag_ranges(self.tag_timer)=}")
        self.search_time_set_tag(sel_end_pos)

    def search_url_set_tag(self, first_index:str="1.0"):
        """
        テキストにタグ付
        説明の内容のurlにタグを付ける

        Args:
            first_index(str):   検索開始位置
        """
        count = tk.IntVar(self, value=0)
        pos = self.t_tips.search("https?://[\w.?=&#%~/-]+", first_index, tk.END, regexp=True, count=count)
        if not pos: return
        sel_end_pos = f"{pos}+{count.get()}c"
        self.t_tips.tag_add(self.tag_url, pos, sel_end_pos)
        logger.debug(f"{self.t_tips.tag_ranges(self.tag_url)=}")
        self.search_url_set_tag(sel_end_pos)

    def add_item(self, event=None):
        """
        レシピを追加
        Dataframeのキーが重複していたらダイアログを出し、再入力させる
        """
        r_name = simpledialog.askstring("料理名入力", "料理名を入力してください")
        if r_name is None: return
        # キーの重複チェック
        a = self.t_inss.get(1.0, tk.END)
        b = self.t_ings.get(1.0, tk.END)
        c = self.t_tips.get(1.0, tk.END)
        if a is None and b is None and c is None: return
        msg = self.my_ctr.add_item(r_name, a, b, c)
        if msg:
            messagebox.showerror("追加エラー", msg)
            self.add_item()
            return
        self.b_save.config(text='保存(変更あり)')   # 保存ボタンの表示変更

    def upd_item(self, event=None):
        """
        レシピを更新
        既存のデータを選択せずに更新しようとするとエラー
        """
        a = self.t_inss.get(1.0, tk.END)
        b = self.t_ings.get(1.0, tk.END)
        c = self.t_tips.get(1.0, tk.END)
        if a is None and b is None and c is None: return
        msg = self.my_ctr.upd_item(self.tv_sel, a, b, c)
        if msg:
            messagebox.showerror("更新エラー", msg)
            return
        self.b_upd.config(text='更新')
        self.b_save.config(text='保存(変更あり)')
        self.b_upd.update_idletasks()

    def del_item(self, event=None):
        """
        レシピを削除
        Dataframeから選択中のデータを削除
        """
        self.my_ctr.del_item(self.tv_sel)           # Dataframeから削除
        self.clear_t_widget()                       # 編集エリアをクリア
        self.b_save.config(text='保存(変更あり)')    # 保存ボタンの表示変更

    def show_url(self, event=None):
        """
        タグ範囲の文字列を取得しブラウザを起動
        """
        i = iter(self.t_tips.tag_ranges(self.tag_url))
        pairs = zip(i, i)                   # tag_rangesの戻り値を2要素ずつのペアにする
        event_idx = event.widget.index(tk.CURRENT)      # マウス位置のインデックスを取得
        # マウス位置のインデックスが範囲に含まれているタグ範囲を抽出
        tag_idx = [(s, e) for s, e in pairs 
                    if self.t_tips.compare(event_idx, ">=", s) 
                    and self.t_tips.compare(event_idx, "<=", e)]
        if len(tag_idx) != 1: return        # 該当タグ範囲は１つのはず
        url = self.t_tips.get(f"{tag_idx[0][0]}", f"{tag_idx[0][1]}")   # タグ範囲の文字列を取得
        webbrowser.open(url, 2)             # デフォルトブラウザで表示

    def start_countdown(self, event=None):
        """
        タグ範囲の文字列を取得し秒に変換しタイマーを起動
        """
        i = iter(self.t_inss.tag_ranges(self.tag_timer))
        pairs = zip(i, i)                   # tag_rangesの戻り値を2要素ずつのペアにする
        event_idx = event.widget.index(tk.CURRENT)      # マウス位置のインデックスを取得
        # マウス位置のインデックスが範囲に含まれているタグ範囲を抽出
        tag_idx = [(s, e) for s, e in pairs 
                    if self.t_inss.compare(event_idx, ">=", s) 
                    and self.t_inss.compare(event_idx, "<=", e)]
        if len(tag_idx) != 1: return        # 該当タグ範囲は１つのはず
        # タグ範囲の文字列を取得、「n分」なので「分」を除いて整数へ、分なので秒へ変換
        rest = int(self.t_inss.get(f"{tag_idx[0][0]}", f"{tag_idx[0][1]}").rstrip('分')) * 60
        self.p_bar.config(maximum=rest)     # プログレスバーの最大値を設定
        self.p_bar.start(1000)              # プログレスバーを1秒ごとに動かす
        self.countdown(rest)                # カウントダウンの起動

    def countdown(self, count:int):
        """
        カウントダウン中の時間の表示

        Args:
            count(int):   残カウント
        """
        if count > 0:
            self.after_id = self.after(1000, self.countdown, count - 1)
        self.cd.set(count)
        m, s = divmod(count, 60)
        r_time = f"{m}:{s:02}"
        self.stl.configure("my_pbar.TProgressbar", text=r_time)
        if count == 0:
            self.p_bar.stop()
            self.do_alarm()

    def do_alarm(self, event=None):
        """
        アラーム用サブプロセスを起動
        """
        # 対象ファイルのパス取得
        if hasattr(sys, "_MEIPASS"):
            tar_path = sys._MEIPASS  # 実行ファイルで起動した場合
        else:
            tar_path = "."  # python コマンドで起動した場合
        path = os.path.join(tar_path, stgs.ALARM)
        logger.debug(f"{path=}")
		# ファイルに関連付けられたアプリケーションを使ってスタート
        os.startfile(path)

class MyModel():
    """
    モデルクラス
    """
    def __init__(self) -> None:
        """
        コンストラクタ：JSONファイルの読み込み
        """
        self.path = "my_recipe.json"
        self.cols = ["names", "inss", "ings", "tips"]
        self.df = pd.DataFrame(columns=self.cols)
        self.df.set_index("names", inplace=True)
        try:
            # JSONデータの読み込み
            self.df = pd.read_json(self.path, orient='split')
            self.df.index.rename("names", inplace=True)
        except Exception as e2:
            messagebox.showerror("ファイルエラー", "ファイルが存在しないので空の状態で起動します")

        # ソート：インデックス(料理名)でソート
        self.df = self.df.sort_index()
        # indexで一番長い文字数のものを求める
        if self.df.index.empty:
            self.max_idx_len = 6 # データがない時
        else:
            self.max_idx_len = self.df.index.str.len().max()    # 全角でも半角でも1文字

    def save(self, event=None):
        """
        DataFrameをJSON形式で保存
        """
        self.df.to_json(self.path, force_ascii=False, orient='split')
        messagebox.showinfo("保存", f"{pathlib.Path.resolve(pathlib.Path(self.path))}に保存しました")

class MyControl():
    """
    コントロールクラス
    """

    def __init__(self, model:MyModel, view:MyFrame) -> None:
        """
        コンストラクタ

        Args:
            model(MyModel):   モデルのオブジェクト
            view(MyFrame):    ビューのオブジェクト
        """
        self.model = model  # モデルオブジェクト
        self.view = view    # ビューオブジェクト

    def save(self):
        """
        DataFrameをJSON形式で保存
        """
        self.model.save()
        self.view.b_save.config(text='保存')
    
    def df_to_ui(self, df:pd.DataFrame, tv:ttk.Treeview, only_idx:bool=True):
        """
        DataFrameをTreeviewに表示

        Args:
            df(DataFrame):  データ
            tv(Treeview):   ツリービュー
            only_idx(bool): ツリービューをインデックスだけで作成
        """
        #  Treeviewのカラム設定。汎用性を考慮してインデックスだけか全てかに対応
        tv_cols = [df.index.name]
        if not only_idx:
            tv_cols = tv_cols + df.columns.to_list()
        tv.config(columns = tv_cols)   # DataFrameのカラム名をTreeviewのcolumnsに設定

        # カラムの幅をインデックスの最大文字数のものに合わせる
        col_width = self.view.tvfont.measure('全' * (self.model.max_idx_len + 1))

        # Treeviewのカラムの見出し、幅を設定
        for cname in tv_cols:
            tv.heading(cname, text=cname)
            tv.column(cname, width=col_width)
        self.df_data_to_ui(df, tv)

    def df_data_to_ui(self, df:pd.DataFrame, tv:ttk.Treeview, sel:str=""):
        """
        DateFrameのIndexの内容をTreeviewに設定(置き換え)

        Args:
            df(DataFrame):  データ
            tv(Treeview):   ツリービュー
            sel(str):       選択するデータ
        """
        tv.delete(*tv.get_children())   # treeviewのデータクリア
        self.view.tv_sel = ""           # treeviewをクリアすると選択状態ではなくなるのでクリア
        with_tag = False                # タグを付加するかどうかのスイッチ
        for x in df.index:
            _tags = []
            if with_tag:
                _tags.append('oddrow')
            with_tag = not with_tag
            iid = tv.insert("", tk.END, values=[x], tags=_tags)
            if x == sel:
                tv.selection_set(iid)   # 選択行を設定
                tv.see(iid)             # 選択行を表示
        tv.update_idletasks()

    def row_to_disp(self, idx:str):
        """
        DataFrameのidx行を画面表示

        Args:
            idx(str): DataFrameのインデックス値
        """
        # dataframeからidx行を取得
        # inss = self.model.df.at[idx, "inss"]
        # ings = self.model.df.at[idx, "ings"]
        # tips = self.model.df.at[idx, "tips"]
        inss, ings, tips = self.model.df.loc[idx, ["inss", "ings", "tips"]]
        # 取得データを画面(テキストウィジェット)に表示
        self.view.insert_t_widget(self.view.t_inss, inss)
        self.view.insert_t_widget(self.view.t_ings, ings)
        self.view.insert_t_widget(self.view.t_tips, tips)

    def add_item(self, r_name:str, r_ins:str, r_ing:str, r_tip:str) -> str:
        """
        画面のデータをDataFrameに追加
        追加後、ツリービューを更新

        Args:
            r_name(str):    料理名(インデックス値)
            r_ins(str):     手順
            r_ing(str):     材料
            r_tip(str):     説明
        Return:
            str:    エラーでない時は空文を返す
                    エラーの時はメッセージを返す
        """
        try:
            if r_name in self.model.df.index:
                return "同じものが既に存在します"
            self.model.df.loc[r_name] = [r_ins, r_ing, r_tip]
            self.df_data_to_ui(self.model.df, self.view.tv, r_name)
            return ""
        except pd.errors.IndexingError as ek:
            return ek

    def upd_item(self, r_name:str, r_ins:str, r_ing:str, r_tip:str) -> str:
        """
        DataFrameの行を更新

        エラーでない時は空文を返す
        エラーの時はメッセージを返す

        Args:
            r_name(str):    料理名(インデックス値)
            r_ins(str):     手順
            r_ing(str):     材料
            r_tip(str):     説明
        Return:
            str:    エラーでない時は空文を返す
                    エラーの時はメッセージを返す
        """
        if not r_name:
            return "新規データなので追加を実施してください"
        try:
            self.model.df.loc[r_name] = [r_ins, r_ing, r_tip]
            return ""
        except pd.errors.IndexingError as ek:
            return ek

    def del_item(self, r_name:str):
        """
        DataFrameの行を削除

        Args:
            r_name(str):    料理名(インデックス値)
        """
        if not r_name: return   # 選択していない場合は何もしない
        self.model.df.drop(r_name, inplace=True)
        # 画面再表示
        self.df_data_to_ui(self.model.df, self.view.tv)

class App(tk.Tk):
    """
    アプリケーションクラス
    """
    def __init__(self) -> None:
        """
        コンストラクタ：操作画面クラスと制御クラスを作成し関連付ける
        """
        super().__init__()
        import tkinter.font as tkFont
        # 定義済みフォントの変更
        tkFont.nametofont("TkDefaultFont").config(size=stgs.FONT_SIZE, family=stgs.FONT)
        tkFont.nametofont("TkTextFont").config(size=stgs.FONT_SIZE, family=stgs.FONT)
        tkFont.nametofont("TkHeadingFont").config(size=stgs.FONT_SIZE, family=stgs.FONT)
        tkFont.nametofont("TkFixedFont").config(size=stgs.FONT_SIZE, family=stgs.FONT)    # テキストウィジェットの中身

        self.title("レシピ")      # タイトル

        my_model = MyModel()

        my_frame = MyFrame(self)                    # MyFrameクラス(V)のインスタンス作成
        my_frame.pack()

        my_ctr = MyControl(my_model, my_frame)      # 制御クラス(C)のインスタンス作成
        my_frame.set_my_ctr(my_ctr)                 # ビューにMyControlクラスを設定
        my_ctr.df_to_ui(my_model.df, my_frame.tv)   # DataFrameのデータをTreeviewに設定
        # treeviewの見出しを変更(上記のメソッドはできるだけ汎用的に作ったので)
        my_frame.tv.heading('names', text='料理名')

        # 画面サイズの保持(Tkinterが作成した初期画面を保持してデータ挿入後に大きくならないようにする)
        self.geometry(self.geometry())

if __name__ == '__main__':
    # logger setting
    LOGLEVEL = "INFO"   # ログレベル('CRITICAL','FATAL','ERROR','WARN','WARNING','INFO','DEBUG','NOTSET')
    logger = getLogger()
    handler = StreamHandler()	# このハンドラーを使うとsys.stderrにログ出力
    handler.setLevel(LOGLEVEL)
    # ログ出形式を定義 時:分:秒.ミリ秒 L:行 M:メソッド名 T:スレッド名 コメント
    handler.setFormatter(Formatter("{asctime}.{msecs:.0f} {name} L:{lineno:0=3} T:{threadName} M:{funcName} : {message}", "%H:%M:%S", "{"))
    logger.setLevel(LOGLEVEL)
    logger.addHandler(handler)
    logger.propagate = False
    logger.debug("start log")

    app = App()
    app.focus_force()   # ダイアログボックスを表示して閉じるとフォーカスが失われるので獲得する
    app.mainloop()
