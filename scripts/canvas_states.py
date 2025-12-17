from scripts.config import DEFAULT_COLOUR, CELL_SIDE_COUNT

pendingUpdates = []
pixelArray = [[{'colour': DEFAULT_COLOUR, 'ip_address': None} 
               for _ in range(CELL_SIDE_COUNT)] 
              for _ in range(CELL_SIDE_COUNT)]