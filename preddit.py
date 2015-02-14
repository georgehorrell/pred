import textwrap, logging, curses, traceback, praw
logging.basicConfig(filename='error.log', level=logging.DEBUG)


# define the program for the user agent
user_agent = "pREDDIT v0.0.1 - reddit-cli agent"

# connect to reddit and return praw.Reddit object
def reddit_connect(user_agent):
	return praw.Reddit(user_agent=user_agent)

def fix_unicode(string):
    return string.encode('utf-8', 'replace')

# base view object, defines dimensions based on curses screen object
class view(object):
    def __init__(self, screen):
        self.update_dims(screen)
        self.exit = False

    def update_dims(self, screen):
        self.dims = screen.getmaxyx()
        self.width = self.dims[1] - 2
        self.height = self.dims[0] - 2
        self.width_centre = self.width / 2
        self.height_centre = self.height / 2
        self.input_buffer_y = self.height
        self.input_buffer_x = 2
        self.lines = self.height - 2

    def call_draw_functions(self, screen):
        pass

    def get_std_input(self, screen):
        pass

    def view_loop(self, screen):
        while self.exit == False:
            screen.clear()
            screen.box()
            self.call_draw_functions(screen)
            self.get_std_input(screen)

    # handle all input
    def get_std_input(self, screen):
        ch = screen.getch()

        # handle terminal resizing by updating the view dimensions
        if ch==curses.KEY_RESIZE:
            self.update_dims(screen)

        elif ch==58:
            # handle complex input preceeded by ':'
            screen.addstr(self.input_buffer_y, self.input_buffer_x, ":")
            curses.echo()
            in_str = screen.getstr()
            if in_str[0] == 'q':
                self.exit=True
            elif in_str[0] == 'r':
                self.subreddit = in_str[2:]
            elif in_str[0] == 'o':
                current_post = post_view(screen, self.content[int(in_str[2:])])
                current_post.view_loop(screen)
            curses.noecho()

# Define view object, stores data about current display and functions to
# display data to screen.
class subreddit_view(view):
    def __init__(self, screen, subreddit, r):
        super(subreddit_view, self).__init__(screen)
        self.subreddit = subreddit
        self.update_dims(screen)
        self.title = "pREDDIT v0.0.1"
        self.exit = False
        self.r = r

    # update content
    def update_content(self):
        if self.subreddit == 'frontpage':
            self.content = list(self.r.get_front_page(limit=self.lines))
        else:
            self.content = list(self.r.get_subreddit(self.subreddit).get_hot(limit=self.lines))

    # draw data to screen object
    def draw_subreddit(self, screen):
        subreddit = '/r/' + self.subreddit
        screen.addstr(self.input_buffer_y, (self.width-len(subreddit)), subreddit)

    # draw title to top centre of screen
    def draw_title(self, screen):
        screen.addstr(0, int( self.width_centre - (len(self.title) / 2)), self.title)

    # render results page of subreddit or frontpage
    def draw_content(self, screen):
        for idx, submission in enumerate(self.content):
            screen.addstr(idx+1, 2, self.format_submission_data(idx, submission))

    # format submission data for results page
    def format_submission_data(self, idx, submission):
        post_len = self.width - 27
        if submission.is_self:
            sub_type = "S"
        elif 'imgur' in submission.url:
            sub_type = "I"
        else:
            sub_type = " "
        out = '[{0:2}] ({1:4}) [{2}] {3} [{4:5}]'.format(idx, submission.ups, sub_type, fix_unicode(submission.title)
                                                                            [:post_len], submission.num_comments)
        return out

    def call_draw_functions(self, screen):
        self.update_content()
        self.draw_title(screen)
        self.draw_content(screen)
        self.draw_subreddit(screen)


class post_view(view):
    def __init__(self, screen, submission):
        super(post_view, self).__init__(screen)
        self.submission = submission
        self.post_title = submission.title
        self.post_selftext = submission.selftext
        self.update_dims(screen)

    def call_draw_functions(self, screen):
        screen.addstr(1, (self.width_centre-(len(self.post_title)/2)), fix_unicode(self.post_title))
        for line, text in enumerate(textwrap.wrap(self.post_selftext, (self.width-5))):
            screen.addstr(3+line, 2, fix_unicode(text))

# main loop
def main(stdscr):
    # define the screen as a subwindow taking up the entire stdscr
    screen = stdscr.subwin(0,0)
    r = reddit_connect(user_agent)
    r.config.decode_html_entities = True
    sub_view = subreddit_view(screen, 'linux', r)

    # main loop
    sub_view.view_loop(screen)

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
