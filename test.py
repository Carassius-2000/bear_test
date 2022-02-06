"""Bearing Vibration Prediction Information System"""
from typing import Dict, List, Tuple, Union
import socket
import wx
import wx.adv
import psycopg2 as pspg2
import matplotlib.pyplot as plt
import numpy as np
import telegram
import matplotlib
import pandas as pd
from matplotlib.backends.backend_wxagg import (
    NavigationToolbar2WxAgg as NavigationToolbar,
    FigureCanvasWxAgg as FigureCanvas)
from matplotlib.figure import Figure
import seaborn as sns
sns.set_theme()
matplotlib.use('WXAgg')

BEARING_LIST: List[str] = ['Первый подшипник',
                           'Второй подшипник',
                           'Третий подшипник']
# MAX_BEARINGS_VIBRATION: List[int] = [5, 2, 3]
MAX_BEARINGS_VIBRATION: Dict[int, int] = {0: 5, 1: 2, 2: 3}
BACKGROUND_COLOR: str = '#fff1e6'
BUTTON_COLOR: str = '#1bc163'
TEXT_COLOR: str = '#000000'


class AuthorizationWindow(wx.Frame):
    """Window that allows user to enter Information System."""

    def __init__(self):
        """Create Authorization Window.

        Attributes:
            login_edit (wx.TextCtrl): Edit that contains user's login.
            password_edit (wx.TextCtrl): Edit that contains user's password.
        """
        super().__init__(parent=None,
                         title='Вход в систему',
                         size=(270, 170),
                         style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU
                         | wx.CAPTION | wx.CLOSE_BOX)
        self.Center()

        panel = wx.Panel(self)
        panel.SetFont(APP_FONT)
        panel.SetBackgroundColour(BACKGROUND_COLOR)
        # create FlexGridSizer that contains login and password edits
        # with their respective labels
        flex_grid_sizer = wx.FlexGridSizer(2, 2, 10, 10)

        login_label = wx.StaticText(panel, label='Логин')
        login_label.SetForegroundColour(TEXT_COLOR)
        self.login_edit = wx.TextCtrl(panel,
                                      size=(170, 30))

        password_label = wx.StaticText(panel, label='Пароль')
        password_label.SetForegroundColour(TEXT_COLOR)
        self.password_edit = wx.TextCtrl(panel,
                                         size=(170, 30),
                                         style=wx.TE_PASSWORD)

        flex_grid_sizer.AddMany([(login_label),
                                 (self.login_edit, wx.ID_ANY, wx.EXPAND),
                                 (password_label),
                                 (self.password_edit, wx.ID_ANY, wx.EXPAND)])
        # add FlexGridSizer to BoxSizer
        box_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(flex_grid_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        enter_button = wx.Button(panel, label='Войти')
        enter_button.SetForegroundColour(TEXT_COLOR)
        enter_button.SetBackgroundColour(BUTTON_COLOR)
        box_sizer.Add(enter_button,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        enter_button.Bind(wx.EVT_BUTTON, self.on_enter_button_click)

        panel.SetSizer(box_sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)

    def on_close_window(self, event) -> None:
        """Close Authorization Window."""
        question: str = 'Вы действительно хотите выйти из приложения?'
        dialog_message = wx.MessageDialog(self,
                                          question,
                                          ' ',
                                          wx.YES_NO | wx.YES_DEFAULT
                                          | wx.ICON_WARNING)
        result: int = dialog_message.ShowModal()
        if result == wx.ID_YES:
            self.Destroy()
        else:
            event.Veto()

    def get_connection(self, username: str, password: str):
        """Get PostgreSQL database connection.

        Args:
            username (str): PostgreSQL user's name.
            password (str): PostgreSQL user's password.

        Returns:
            PostgreSQL connection.

        Raises:
            psycopg2.OperationalError: If username or password is invalid.
        """
        connection_string: str = \
            f'dbname=testdb user={username} password={password}'
        try:
            connection: Union[pspg2.extensions.connection,
                              None] = pspg2.connect(connection_string)
        except pspg2.OperationalError:
            error_text: str = 'Введен неверный логин или пароль.'
            dialog_message = wx.MessageDialog(self,
                                              error_text,
                                              ' ',
                                              wx.OK | wx.ICON_ERROR)
            dialog_message.ShowModal()
            return
        else:
            return connection

    def on_enter_button_click(self, event) -> None:
        """Enter Information System."""
        login: str = self.login_edit.GetValue()
        password: str = self.password_edit.GetValue()
        if check_internet_connection():
            connection = self.get_connection(login, password)
            if connection:
                self.Destroy()
                main_frame = MainWindow(self.font, db_connection=connection)
                main_frame.Show()


class MainWindow(wx.Frame):

    def __init__(self, db_connection=None):
        super().__init__(parent=None,
                         title='Основное окно',
                         size=(310, 240),
                         style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU
                         | wx.CAPTION | wx.CLOSE_BOX)
        self.Center()

        panel = wx.Panel(self)
        panel.SetFont(APP_FONT)
        panel.SetBackgroundColour(BACKGROUND_COLOR)

        box_sizer = wx.BoxSizer(wx.VERTICAL)

        self.bearing_choice = wx.Choice(panel, choices=BEARING_LIST)
        self.bearing_choice.SetSelection(0)
        box_sizer.Add(self.bearing_choice,
                      flag=wx.EXPAND | wx.ALL, border=10)

        select_button = wx.Button(panel, label='Выбрать дату прогноза')
        select_button.SetForegroundColour(TEXT_COLOR)
        select_button.SetBackgroundColour(BUTTON_COLOR)
        box_sizer.Add(select_button,
                      flag=wx.EXPAND |
                      wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=10)
        select_button.Bind(wx.EVT_BUTTON, self.on_select_button_click)

        # self.df = None
        y = np.arange(1, 11)
        y_mn = y - 1
        y_mx = y + 1
        self.df = pd.DataFrame({'date': np.arange(1, len(y) + 1),
                                'val': y,
                                'val_max': y_mx,
                                'val_min': y_mn})

        visualization_button = wx.Button(panel, label='Визуализация процесса')
        visualization_button.SetForegroundColour(TEXT_COLOR)
        visualization_button.SetBackgroundColour(BUTTON_COLOR)
        box_sizer.Add(visualization_button,
                      flag=wx.EXPAND |
                      wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=10)
        visualization_button.Bind(wx.EVT_BUTTON,
                                  self.on_visualization_button_click)

        send_message_button = wx.Button(panel, label='Отправить сообщение')
        send_message_button.SetForegroundColour(TEXT_COLOR)
        send_message_button.SetBackgroundColour(BUTTON_COLOR)
        box_sizer.Add(send_message_button,
                      flag=wx.EXPAND
                      | wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=10)
        send_message_button.Bind(
            wx.EVT_BUTTON, self.on_send_message_button_click)

        save_prediction_button = wx.Button(panel, label='Записать прогноз')
        save_prediction_button.SetForegroundColour(TEXT_COLOR)
        save_prediction_button.SetBackgroundColour(BUTTON_COLOR)

        box_sizer.Add(save_prediction_button,
                      flag=wx.EXPAND |
                      wx.LEFT | wx.RIGHT | wx.BOTTOM,
                      border=10)

        panel.SetSizer(box_sizer)

        self.Bind(wx.EVT_CLOSE, self.on_close_window)

    def on_close_window(self, event):
        question: str = 'Вы действительно хотите выйти из приложения?'
        dialog_message = wx.MessageDialog(self,
                                          question,
                                          ' ',
                                          wx.YES_NO | wx.YES_DEFAULT
                                          | wx.ICON_WARNING)
        result = dialog_message.ShowModal()

        if result == wx.ID_YES:
            self.Destroy()
        else:
            event.Veto()

    def on_select_button_click(self, event):
        with SelectDataWindow(self) as select_data_dialog:
            select_data_dialog.ShowModal()

    def prediction_intervals(self, y_r: np.ndarray) -> Tuple[
            np.ndarray, np.ndarray]:
        '''Prediction interval'''
        std = y_r.std()
        koef = 2.1701
        yr_min = y_r - round(koef * std, 8)
        yr_max = y_r + round(koef * std, 8)
        return yr_min, yr_max

    def on_visualization_button_click(self, event) -> None:
        bearing_type: int = self.bearing_choice.GetCurrentSelection()
        with PlotWindow(self, self.df, bearing_type) as plot_window_dialog:
            plot_window_dialog.ShowModal()

    def on_send_message_button_click(self, event):
        with SendMessageWindow(self) as send_message_dialog:
            send_message_dialog.ShowModal()


class SelectDataWindow(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent=parent,
                         title='Выбрать дату прогноза',
                         size=(300, 170),
                         style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU
                         | wx.CAPTION | wx.CLOSE_BOX)
        self.Center()

        panel = wx.Panel(self)
        panel.SetFont(APP_FONT)
        panel.SetBackgroundColour(BACKGROUND_COLOR)

        flex_grid_sizer = wx.FlexGridSizer(2, 2, 10, 10)

        date_begin_label = wx.StaticText(panel, label='C')
        date_begin_edit = wx.adv.DatePickerCtrl(panel,
                                                style=wx.adv.DP_DROPDOWN,
                                                size=(230, 30))

        date_end_label = wx.StaticText(panel, label='По')
        date_end_edit = wx.adv.DatePickerCtrl(panel,
                                              style=wx.adv.DP_DROPDOWN,
                                              size=(230, 30))

        flex_grid_sizer.AddMany([(date_begin_label),
                                 (date_begin_edit, wx.ID_ANY, wx.EXPAND),
                                 (date_end_label),
                                 (date_end_edit, wx.ID_ANY, wx.EXPAND)])

        box_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(flex_grid_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        enter_button = wx.Button(panel, label='Спрогнозировать')
        enter_button.SetForegroundColour(TEXT_COLOR)
        enter_button.SetBackgroundColour(BUTTON_COLOR)
        box_sizer.Add(enter_button,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        panel.SetSizer(box_sizer)


class CanvasPanel(wx.Panel):
    """Panel that contains canvas with plot on it."""

    def __init__(self, parent):
        """Create Canvas Panel.

        Args:
            parent: Parent class reference.

        Attributes:
            axes (matplotlib.axes._subplots.AxesSubplot): \
                Axes that contain plots.
        """
        super().__init__(parent)

        figure = Figure()
        self.axes = figure.add_subplot(111)

        box_sizer = wx.BoxSizer(wx.VERTICAL)

        canvas = FigureCanvas(self, -1, figure)
        box_sizer.Add(canvas, 1, wx.LEFT | wx.TOP | wx.GROW)

        toolbar = NavigationToolbar(canvas)
        toolbar.Realize()
        box_sizer.Add(toolbar, 0, wx.LEFT | wx.EXPAND)

        self.SetSizer(box_sizer)
        self.Fit()

    def get_outliers(self,
                     df: pd.core.frame.DataFrame,
                     bearing_type: int) -> pd.core.frame.DataFrame:
        """Get outliers DataFrame.

        Args:
            df (pd.core.frame.DataFrame): DataFrame that contain fitted values\
                with prediction interval.
                bearing_type (int): .

        Returns:
            pd.core.frame.DataFrame: DataFrame that contain outliers.
        """
        condition: bool = df['val'] > MAX_BEARINGS_VIBRATION[bearing_type]
        df_out = pd.DataFrame({'val': df[condition].val,
                               'date': df[condition].date})
        return df_out

    def show_plot(self,
                  df: pd.core.frame.DataFrame,
                  bearing_type: int) -> None:
        """Show plot with predictions.

        Args:
            df (pd.core.frame.DataFrame): DataFrame that contain fitted values\
                with prediction interval.
        """
        bearing_name: str = BEARING_LIST[bearing_type]
        self.axes.plot(df['date'], df['val'],
                       label='Прогнозные значения', color='blue')
        self.axes.plot(df['date'], df['val_min'],
                       linestyle='--', color='cyan',
                       label='Минимальные прогнозные значения')
        self.axes.plot(df['date'], df['val_max'],
                       linestyle='--', color='orange',
                       label='Максимальные прогнозные значения')

        outlier_df = self.get_outliers(df, bearing_type=0)
        if not outlier_df.empty:
            self.axes.plot(outlier_df.date,
                           outlier_df.val,
                           linestyle='', marker='o',
                           color='red', label='Аномальные значения')
        self.axes.set_title(f'{bearing_name}', fontsize=12)
        self.axes.set_xlabel('Время', fontsize=12)
        self.axes.set_ylabel('Вибрация (мкм)', fontsize=12)
        self.axes.legend(loc='best', shadow=True, fontsize=12)


class PlotWindow(wx.Dialog):
    """Window that shows bearing vibration plot."""

    def __init__(self, parent, 
                 df: pd.core.frame.DataFrame,
                 bearing_type: int):
        """Create Plot Window.

        Args:
            parent: Parent class reference.

        Attributes:
            panel (CanvasPanel): Panel that contains canvas with plot.
        """
        super().__init__(parent=parent,
                         title='Окно визуализации',
                         size=(620, 620),
                         style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU
                         | wx.CAPTION | wx.CLOSE_BOX
                         | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX)
        self.Center()

        self.panel = CanvasPanel(self)

        self.panel.show_plot(df, bearing_type)


class SendMessageWindow(wx.Dialog):
    """Window that allows user to send message to engineer."""

    def __init__(self, parent=None):
        """Create Send Message Window.

        Args:
            parent: Parent class reference.

        Attributes:
            bearing_choice (wx.Choice): Choice that contains bearing types.
            date_edit (wx.adv.DatePickerCtrl):\
            Edit that contains user's password.
        """
        super().__init__(parent=parent,
                         title='Отправка сообщения',
                         size=(290, 170),
                         style=wx.MINIMIZE_BOX | wx.SYSTEM_MENU
                         | wx.CAPTION | wx.CLOSE_BOX)
        self.Center()

        panel = wx.Panel(self)
        panel.SetFont(APP_FONT)
        panel.SetBackgroundColour(BACKGROUND_COLOR)

        flex_grid_sizer = wx.FlexGridSizer(2, 2, 10, 10)

        change_bearing_label = wx.StaticText(panel, label='Заменить')
        self.bearing_choice = wx.Choice(panel, choices=BEARING_LIST)
        self.bearing_choice.SetSelection(0)

        date_label = wx.StaticText(panel, label='До')
        self.date_edit = wx.adv.DatePickerCtrl(panel,
                                               style=wx.adv.DP_DROPDOWN,
                                               size=(170, 30))

        flex_grid_sizer.AddMany([(change_bearing_label),
                                 (self.bearing_choice,
                                  wx.ID_ANY, wx.EXPAND),
                                 (date_label),
                                 (self.date_edit, wx.ID_ANY, wx.EXPAND)])

        box_sizer = wx.BoxSizer(wx.VERTICAL)
        box_sizer.Add(flex_grid_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        enter_button = wx.Button(panel, label='Отправить')
        enter_button.SetForegroundColour(TEXT_COLOR)
        enter_button.SetBackgroundColour(BUTTON_COLOR)
        box_sizer.Add(enter_button,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        enter_button.Bind(wx.EVT_BUTTON, self.on_enter_button_click)

        panel.SetSizer(box_sizer)

    def on_enter_button_click(self, event) -> None:
        """Send message and show message dialog."""
        bearing_type: str = BEARING_LIST[
            self.bearing_choice.GetCurrentSelection()]
        date: str = str(self.date_edit.GetValue()).split()[0]
        with open('token.txt', 'r') as token_file:
            for t in token_file:
                token: str = t
        if check_internet_connection():
            self.send_message(bearing_type, date, token)
            dialog_text: str = 'Сообщение успешно отправлено'
            dialog_message = wx.MessageDialog(self,
                                              dialog_text,
                                              ' ',
                                              wx.OK | wx.ICON_INFORMATION)
            dialog_message.ShowModal()

    def send_message(self, bearing: int, date: str, token: str) -> None:
        """Send message to Telegram bot.

        Args:
            bearing (int): Bearing type that need to be replaced.
            date (str): Date by which the bearing must be replaced.
            token (str): Telegram Bot Token.

        Raises:
            IndexError: If there aren't messages in the chat.
        """
        bot = telegram.Bot(token=token)
        try:
            chat_id: int = bot.get_updates()[-1].message.chat_id
        except IndexError:
            chat_id: int = 0
        finally:
            bot.send_message(
                chat_id=chat_id,
                text=f'{bearing} необходимо заменить до {date}')


def internet_connection_fail() -> None:
    """Show internet connection error dialog."""
    error_text: str = 'Проверьте подключение к интернету.'
    error_message = wx.MessageDialog(None,
                                     error_text,
                                     ' ',
                                     wx.OK | wx.ICON_ERROR)
    error_message.ShowModal()


def check_internet_connection() -> bool:
    """Try to ping www.google.com.

    Returns:
        bool: True if the attempt was successful.
    """
    try:
        socket.create_connection(("www.google.com", 80))
    except OSError:
        internet_connection_fail()
    else:
        return True


if __name__ == '__main__':
    app = wx.App()
    # get OS default font
    APP_FONT = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
    APP_FONT.SetPointSize(12)

    # authorization_frame = AuthorizationWindow()
    # authorization_frame.Show()
    main_frame = MainWindow()
    main_frame.Show()

    app.MainLoop()
