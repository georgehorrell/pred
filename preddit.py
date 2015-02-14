import logging, curses, traceback, praw
logging.basicConfig(filename='error.log', level=logging.DEBUG)


# define the program for the user agent
user_agent = "pREDDIT v0.0.1 - reddit-cli agent"
title = "pREDDIT v0.0.1"
limit = 45

# connect to reddit and return praw.Reddit object
def reddit_connect(user_agent):
	return praw.Reddit(user_agent=user_agent)

# define view object, stores data about current display
class view(object):
    def __init__(self, screen):
        self.is_results = True
        self.is_submission = False
        self.update_dims(screen)

    def update_dims(self, screen):
        self.dims = screen.getmaxyx()
        self.width = self.dims[1] - 2
        self.height = self.dims[0] - 2
        self.width_centre = self.width / 2
        self.height_centre = self.height / 2
        self.input_buffer_y = self.height
        self.input_buffer_x = 2
        self.lines = self.height - 2

# format submission data for results page
def format_submission_data(idx, submission, view):
    post_len = view.width - 19
    if submission.is_self:
        self = "S"
    else:
        self = " "
    out = '[{0:2}] ({1:4}) [{2}] {3}'.format(idx, submission.ups, self, submission.title.encode('utf-8',
                                                                        'replace')[:post_len])
    return out

# format current view data for display
def format_view_data(current_view):
    if current_view.is_results == True:
        out = current_view.subreddit
    elif current_view.is_submission == True:
        out = current_view.submission.title.encode('utf-8', 'replace')


# render results page of subreddit or frontpage
def draw_page(content, screen, view):
    if view.is_results == True:
        for idx, submission in enumerate(content):
            screen.addstr(idx+1, 2, format_submission_data(idx, submission, view))


# draw title to top centre of screen
def draw_title(screen, view):
    screen.addstr(0, int( view.width_centre - (len(title) / 2)), title) #render the title

# parse complex input
def parse_input(in_str):
    try:
        if in_str[0]=='q':
            return 'q'
    except:
        return 0

# handle all input
def get_std_input(screen, view):
    global exit
    ch = screen.getch()

    # handle terminal resizing by updating the view dimensions
    if ch==curses.KEY_RESIZE:
        view.update_dims(screen)
    elif ch==58:
        # handle complex input preceeded by ':'
        screen.addstr(view.input_buffer_y, view.input_buffer_x, ":")
        curses.echo()
        in_str = screen.getstr()
        if parse_input(in_str) == 'q':
            exit=True
        elif parse_input(in_str) == 0:
            screen.addstr(view.input_buffer_x, view.input_buffer_y, "Invalid input.")
        curses.noecho()



# main loop
def main(stdscr):
    # define the screen as a subwindow taking up the entire stdscr
    screen = stdscr.subwin(0,0)
    global exit
    exit = False # exit variable, triggered with q as input
    r = reddit_connect(user_agent)
    r.config.decode_html_entities = True
    current_view = view(screen)
    # main loop
    current_view.is_results = True
    while exit==False:
        screen.border(0)

        draw_title(screen, current_view)
        front_page = r.get_front_page(limit=current_view.lines)
        draw_page(front_page, screen, current_view)
        get_std_input(screen, current_view)
        screen.clear()

    screen.refresh()

if __name__=='__main__':
  try:
      # Initialize curses
      stdscr=curses.initscr()
      # Turn off echoing of keys, and enter cbreak mode,
      # where no buffering is performed on keyboard input
      curses.noecho()
      curses.cbreak()

      # In keypad mode, escape sequences for special keys
      # (like the cursor keys) will be interpreted and
      # a special value like curses.KEY_LEFT will be returned
      stdscr.keypad(1)
      main(stdscr)                    # Enter the main loop
      # Set everything back to normal
      stdscr.keypad(0)
      curses.echo()
      curses.nocbreak()
      curses.endwin()                 # Terminate curses
  except:
      # In event of error, restore terminal to sane state.
      stdscr.keypad(0)
      curses.echo()
      curses.nocbreak()
      curses.endwin()
      traceback.print_exc()           # Print the exception
