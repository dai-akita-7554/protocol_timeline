import re
import datetime
from graphviz import Digraph

class Procedure:
    def __init__(self, id = None, label = None, place = None, 
        start = None, end = None, date = None, prev = []):
        self.id = id
        self.label = label
        self.place = place
        self.start = start
        self.end = end
        self.date = date
        self.prev = prev

        self.t = None
        self.wait = {}

    def __repr__(self):
        return self.label
    
    def __str__(self):
        return self.id
    

class Timeline:
    def __init__(self):
        self.procedures = []
        self.t_max = 0
    
    def append(self, new_proc):
        re_time= re.compile(r'([0-9][0-9]?:[0-9][0-9])')
        if new_proc.start is None:
            new_proc.t = self.t_max
            self.t_max += 1
        else:
            same_match = re.match(r'\[(.+)\]', new_proc.start)
            relative_match = re.match(r'([^\+-]+)\+([0-9][0-9]?):([0-9][0-9])', new_proc.start)
            if same_match:
                # case: same start time
                for proc in self:
                    if proc.id == same_match.groups()[0]:
                        new_proc.t = proc.t
                        break
                else:
                    # could not found referred id
                    new_proc.t = self.t_max
                    self.t_max += 1
            elif relative_match:
                # case: relative start time
                target, hour, minute = relative_match.groups()
                for proc in self:
                    if proc.id == target:
                        break
                new_proc.wait[proc.id] = hour + ':' + minute

                if proc.end is not None:
                    target_match = re_time.match(proc.end)
                    if target_match:
                        print(target_match.groups()[0])
                        print(new_proc.start)
                        base_time = datetime.datetime.strptime(
                            target_match.groups()[0], '%H:%M')
                        new_proc.start = (
                            base_time + datetime.timedelta(hours = int(hour), minutes=int(minute))
                        ).strftime('%H:%M')
                        print(new_proc.start)
                    else:
                        new_proc.start = None
                else:
                    new_proc.start = None

                new_proc.t = self.t_max
                self.t_max += 1
            else:
                new_proc.t = self.t_max
                self.t_max += 1

        self.procedures.append(new_proc)
    
    def __len__(self):
        return len(self.procedures)
    
    def __iter__(self):
        return iter(self.procedures)
    
    def __getitem__(self, item):
        return(self.procedures[item])
    
    def __repr__(self):
        return repr(self.procedures)
    
    def __str__(self):
        return str(self.procedures)

    def compile(self, format='pdf', fontname=None):
        re_time= re.compile(r'([0-9][0-9]?:[0-9][0-9])')

        dot = Digraph(format='pdf')
        dot.attr('graph', newrank='true')
        if fontname is not None:
            dot.attr('node', fontname=fontname)
            dot.attr('edge', fontname=fontname)
            dot.attr('graph', fontname=fontname)
        
        # first loop: make times
        prev_date = None
        i_done = []
        for proc in self:
            # print(i_done)
            if proc.t in i_done:
                continue
            else:
                i = proc.t
                i_done.append(i)
            # print(i)
            if proc.date is not None:
                dot.node(f'date{i}', 
                    shape = 'plaintext',
                    label=proc.date)
                if prev_date is not None:
                    dot.edge(prev_date, f'date{i}',
                        style = 'invisible', 
                        arrowhead = 'none')
                prev_date = f'date{i}'

            dot.node(f'time{i}', 
                shape = 'plaintext',
                label = proc.start if proc.start is not None else '')
            if i > 0:
                dot.edge(f'time{i-1}', f'time{i}', 
                    style = 'invisible', 
                    arrowhead = 'none')

            # print('rank')
            if proc.date is not None:
                # print(f'same: date{i}; time{i};')
                dot.body.append('{rank=same; date' + str(i) + '; time' + str(i) + ';}')
        
        # second loop: add procedure nodes
        for place in set([p.place for p in self]):
            if place is not None:
                with dot.subgraph(name=f'cluster_{place}') as sg:
                    sg.attr(label=place)
                    for proc in self:
                        if proc.place == place:
                            sg.node(proc.id, 
                                shape = 'box', 
                                label = proc.label)
            else:
                for proc in self:
                    if proc.place is None:
                        dot.node(proc.id, 
                            shape = 'box', 
                            label = proc.label)
                    
        # third loop: bind procedure nodes
        for proc in self:
            # print(proc.wait)
            for id_prev in proc.prev:
                dot.edge(id_prev, proc.id, 
                    label=proc.wait.get(id_prev, ''))
            if proc.start is not None:
                if re_time.match(proc.start):
                    dot.edge(f'time{proc.t}', proc.id, 
                        style = 'dashed', 
                        arrowhead = 'none')
            dot.body.append('{rank=same; time' + str(proc.t) + '; ' + proc.id + ';}')

        dot.body.append('{rank=min; time0}')
        dot.body.append('{rank=max; time' + str(self.t_max-1) + '}')
        # dot.attr('rank', 'min; time0')
        # dot.attr('rank', f'max; time{len(self.procedures)}')

        self.dot = dot

    def render(self, filename):
        self.dot.render(filename)
    
def from_md(mdfile):
    with open(mdfile, 'r', encoding='utf8') as f:
        lines = f.read().splitlines()

    iter_line = iter(lines)

    # skip until body
    re_body = re.compile('^ *<!-+ body -+>')
    while(not re_body.match(next(iter_line))):
        pass

    re_date = re.compile('# (.*)')
    re_proc = re.compile('## (.*)')
    re_proc_detail = {
        'id': re.compile('\*(.*)\*'),
        'label': re.compile(' ([^*_@<]*) *'),
        'place': re.compile('@([^*_<]*)'),
        'start': re.compile('_(.*)~'),
        'end': re.compile('~(.*)_'),
        'prev': re.compile('<!-+ (.*) -+>')
    }

    tl = Timeline()
    try:
        i_line = next(iter_line, None)
        last_date = None
        while(i_line is not None):
            # print(i_line)

            i_date = re_date.match(i_line)
            i_proc = re_proc.match(i_line)
            if i_date:
                # print('date')
                last_date = i_date.groups()[0]
            elif i_proc:
                # print('proc')
                arg_dict = {}
                for k, v in re_proc_detail.items():
                    i_search = v.search(i_proc.groups()[0])
                    if i_search:
                        arg_dict[k] = i_search.groups()[0]
                    else:
                        arg_dict[k] = None
                if arg_dict['prev'] is not None:
                    arg_dict['prev'] = arg_dict['prev'].split(', ')
                else:
                    arg_dict['prev'] = []
                arg_dict['date'] = last_date
                last_date = None
                # print(arg_dict)
                tl.append(Procedure(**arg_dict))

            i_line = next(iter_line, None)
    except StopIteration:
        pass

    return tl

