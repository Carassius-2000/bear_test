import wx


class AuthorizationWindow(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title='Вход в систему', size=(270, 170))
        self.Center()

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(12)

        panel = wx.Panel(self)
        panel.SetFont(font)
        panel.SetBackgroundColour('#eea588')

        box_sizer = wx.BoxSizer(wx.VERTICAL)

        flex_grid_sizer = wx.FlexGridSizer(2, 2, 10, 10)

        login_label = wx.StaticText(panel, label='Логин')
        login_edit = wx.TextCtrl(panel, size=(170, 30))

        password_label = wx.StaticText(panel, label='Пароль')
        password_edit = wx.TextCtrl(panel, size=(170, 30))

        flex_grid_sizer.AddMany([(login_label),
                                 (login_edit, wx.ID_ANY, wx.EXPAND),
                                 (password_label),
                                 (password_edit, wx.ID_ANY, wx.EXPAND)])

        box_sizer.Add(flex_grid_sizer, flag=wx.EXPAND | wx.ALL, border=10)

        enter_button = wx.Button(panel, label='Войти')
        box_sizer.Add(enter_button,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)

        panel.SetSizer(box_sizer)


class SelectDataWindow(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent=parent, title='Выбрать дату прогноза', size=(320, 170))
        self.Center()

        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(12)

        panel = wx.Panel(self)
        panel.SetFont(font)
        panel.SetBackgroundColour('#ee0588')

        box_sizer = wx.BoxSizer(wx.VERTICAL)

        flex_grid_sizer = wx.FlexGridSizer(2, 2, 10, 10)

        date_begin_label = wx.StaticText(panel, label='C')
        date_begin_edit = wx.TextCtrl(panel, size=(260, 30))

        date_end_label = wx.StaticText(panel, label='По')
        date_end_edit = wx.TextCtrl(panel, size=(260, 30))

        flex_grid_sizer.AddMany([(date_begin_label),
                                 (date_begin_edit, wx.ID_ANY, wx.EXPAND),
                                 (date_end_label),
                                 (date_end_edit, wx.ID_ANY, wx.EXPAND)])

        box_sizer.Add(flex_grid_sizer, flag=wx.EXPAND | wx.ALL, border=10)
        
        enter_button = wx.Button(panel, label='Спрогнозировать')
        box_sizer.Add(enter_button,
                      flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        
        panel.SetSizer(box_sizer)


app = wx.App()

# main_frame = AuthorizationWindow(None)
# main_frame.Show()

select_frame = SelectDataWindow(None)
select_frame.Show()

app.MainLoop()
