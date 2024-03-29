import pygame

pygame.font.init()
images = {'and': pygame.image.load(r'img\and_gate.png'), 'nand': pygame.image.load(r'img\nand_gate.png'),
          'or': pygame.image.load(r'img\or_gate.png'), 'nor': pygame.image.load(r'img\nor_gate.png'),
          'xor': pygame.image.load(r'img\xor_gate.png'), 'xnor': pygame.image.load(r'img\xnor_gate.png'),
          'buffer': pygame.image.load(r'img\buffer_gate.png'), 'not': pygame.image.load(r'img\not_gate.png'),
          'sr_big': pygame.image.load(r'img\sr.png'), 'sr_small': pygame.image.load(r'img\sr_small.png'),
          'jk_big': pygame.image.load(r'img\jk.png'), 'jk_small': pygame.image.load(r'img\jk_small.png'),
          'd_big': pygame.image.load(r'img\d.png'), 'd_small': pygame.image.load(r'img\d_small.png'),
          't_big': pygame.image.load(r'img\t.png'), 't_small': pygame.image.load(r'img\t_small.png'),
          'switch_off': pygame.image.load(r'img\switch_off.png'), 'switch_on': pygame.image.load(r'img\switch_on.png'),
          'bulb_off': pygame.image.load(r'img\bulb_off.png'), 'bulb_on': pygame.image.load(r'img\bulb_on.png'),
          'button_on': pygame.image.load(r'img\button_on.png'), 'button_off': pygame.image.load(r'img\button_off.png')}
tables = {'and': [False, False, False, True], 'nand': [True, True, True, False], 'or': [False, True, True, True],
          'nor': [True, False, False, False], 'xor': [False, True, True, False], 'xnor': [True, False, False, True],
          'buffer': [False, True], 'not': [True, False], 'sr': [False, True, True, True, False, False, False, True],
          'jk': [False, True, True, True, False, False, True, False], 'd': [False, False, True, True],
          't': [False, False, True, False]}
input_counts = {'and': 2, 'nand': 2, 'or': 2, 'nor': 2, 'xor': 2, 'xnor': 2, 'buffer': 1, 'not': 1, 'sr': 2, 'jk': 4,
                'd': 3, 't': 3}
clock_inputs = {'sr': -1, 'jk': 1, 'd': 1, 't': 1}
reset_inputs = {'sr': -1, 'jk': 3, 'd': 2, 't': 2}


class Wire:
    def __init__(self, input, input_num, output, output_num):
        self.input = input
        self.input_num = input_num
        self.output = output
        self.output_num = output_num
        self.state = False
        self.input.add_output(self, self.input_num)
        self.output.set_input(self, self.output_num)

    def start_pos(self):
        input_pos = self.input.pos
        input_offset = self.input.output_offsets[self.input_num]
        return [input_pos[0] + input_offset[0], input_pos[1] + input_offset[1]]

    def end_pos(self):
        output_pos = self.output.pos
        output_offset = self.output.input_offsets[self.output_num]
        return [output_pos[0] + output_offset[0], output_pos[1] + output_offset[1]]

    def update(self):
        self.state = self.input.output_vals[self.input_num]

    def delete(self):
        self.input.remove_output(self, self.input_num)
        self.output.set_input(None, self.output_num)


class Component:
    def __init__(self, pos, size, full_size, input_count, output_count):
        self.pos = pos
        self.size = size
        self.full_size = full_size
        self.input_count = input_count
        self.inputs = [None] * input_count
        self.input_vals = [False] * input_count
        self.input_offsets = []
        x = self.full_size[0] // 2 - 2
        for i in range(input_count):
            self.input_offsets.append([-x, self.get_y_offset(i, input_count)])
        self.output_count = output_count
        self.outputs = []
        self.output_vals = [False] * output_count
        self.output_offsets = []
        for i in range(output_count):
            self.outputs.append([])
            self.output_offsets.append([x, self.get_y_offset(i, output_count)])

    def set_input(self, wire, num):
        self.inputs[num] = wire
        if wire is None:
            self.input_vals[num] = False

    def add_output(self, wire, num):
        self.outputs[num].append(wire)

    def remove_output(self, wire, num):
        self.outputs[num].remove(wire)

    def update(self):
        for i, wire in enumerate(self.inputs):
            if wire is not None:
                self.input_vals[i] = wire.state
        self.calculate()

    def get_y_offset(self, i, count):
        def spread(n, start1, stop1, start2, stop2):
            return round(((n - start1) / (stop1 - start1)) * (stop2 - start2) + start2)
        if count == 1:
            return 0
        limit = self.size[1] // 2 - 5
        return spread(i, 0, count - 1, -limit, limit)

    def calculate(self):
        pass

    def get_image(self):
        pass

    def copy(self):
        pass


class Gate(Component):
    def __init__(self, name, pos):
        self.name = name
        self.table = tables[name]
        self.img = images[name]
        Component.__init__(self, pos, [31, 31], [59, 31], input_counts[name], 1)

    def calculate(self):
        if self.input_count == 1:
            self.output_vals[0] = self.table[1 if self.input_vals[0] else 0]
        else:
            self.output_vals[0] = self.table[sum([2 ** i for i, v in enumerate(self.input_vals) if v])]

    def get_image(self):
        return self.img

    def copy(self):
        return Gate(self.name, self.pos)


class FlipFlop(Component):
    def __init__(self, name, pos):
        self.name = name
        self.clock_input = clock_inputs[name]
        self.reset_input = reset_inputs[name]
        self.img = images[f'{name}_big']
        self.img_small = images[f'{name}_small']
        self.table = tables[name]
        self.clock_prev = False
        size = self.img.get_size()
        Component.__init__(self, pos, [size[0] - 28, size[1]], size, input_counts[name], 2)

    def calculate(self):
        if self.reset_input >= 0 and self.input_vals[self.reset_input]:
            self.output_vals[0] = False
        else:
            if self.clock_input < 0 or not self.clock_prev and self.input_vals[self.clock_input]:
                count = 1
                num = 0
                for i, v in enumerate(self.input_vals):
                    if i not in [self.clock_input, self.reset_input]:
                        if v:
                            num += 2 ** count
                        count += 1
                if self.output_vals[0]:
                    num += 1
                self.output_vals[0] = self.table[num]
        self.output_vals[1] = not self.output_vals[0]
        if self.clock_input >= 0:
            self.clock_prev = self.input_vals[self.clock_input]

    def get_image(self):
        return self.img

    def copy(self):
        return FlipFlop(self.name, self.pos)


class Switch(Component):
    def __init__(self, name, pos):
        self.state = False
        self.name = name
        Component.__init__(self, pos, [31, 31], [59, 31], 0, 1)

    def switch(self):
        self.state = not self.state

    def calculate(self):
        self.output_vals[0] = self.state

    def get_image(self):
        return images['switch_on'] if self.state else images['switch_off']

    def copy(self):
        return Switch(self.name, self.pos)


class Bulb(Component):
    def __init__(self, name, pos):
        self.state = False
        self.name = name
        Component.__init__(self, pos, [31, 31], [59, 31], 1, 0)

    def calculate(self):
        self.state = self.input_vals[0]

    def get_image(self):
        return images['bulb_on'] if self.state else images['bulb_off']

    def copy(self):
        return Bulb(self.name, self.pos)


class Button(Component):
    def __init__(self, name, pos):
        self.name = name
        self.state = False
        Component.__init__(self, pos, [31, 31], [59, 31], 0, 1)

    def set_state(self, state):
        self.state = state

    def calculate(self):
        self.output_vals[0] = self.state

    def get_image(self):
        return images['button_on'] if self.state else images['button_off']

    def copy(self):
        return Button('', self.pos)


class Display(Component):
    def __init__(self, name, pos):
        self.state = 0
        self.name = name
        Component.__init__(self, pos, [31, 51], [59, 51], 4, 0)

    def calculate(self):
        self.state = sum([2 ** (3 - i) for i, v in enumerate(self.input_vals) if v])

    def get_image(self):
        return display_images[self.state]

    def copy(self):
        return Display(self.name, self.pos)


class IntegratedCircuit(Component):
    small_font = pygame.font.Font(None, 14)
    big_font = pygame.font.Font(None, 12)

    def __init__(self, name, inputs, outputs, components, wires, pos, image = None, image_small = None):
        width = 101
        if image is None:
            height = (max(len(inputs), len(outputs)) + 1) * 10 + 1
            self.img = pygame.Surface([width, height], pygame.SRCALPHA, 32)
            self.img_small = pygame.Surface([59, 31], pygame.SRCALPHA, 32)
        else:
            height = image.get_size()[1]
            self.img = image
            self.img_small = image_small
        self.name = name
        self.input_comps = inputs
        self.output_comps = outputs
        self.components = components
        self.wires = wires
        Component.__init__(self, pos, [width - 28, height], self.img.get_size(), len(inputs), len(outputs))
        if image is None:
            self.draw_image()

    def draw_image(self):
        pygame.draw.rect(self.img, [255, 255, 255], [14, 0, self.full_size[0] - 28, self.full_size[1]])
        pygame.draw.rect(self.img, [0, 0, 0], [14, 0, self.full_size[0] - 28, self.full_size[1]], 1)
        for t, arr in enumerate([self.input_offsets, self.output_offsets]):
            for i, (x, y) in enumerate(arr):
                rx = x + self.full_size[0] // 2
                ry = y + self.full_size[1] // 2
                pygame.draw.line(self.img, [0, 0, 0], [rx - 1, ry - 2], [rx + 1, ry - 2])
                pygame.draw.line(self.img, [0, 0, 0], [rx - 1, ry + 2], [rx + 1, ry + 2])
                pygame.draw.line(self.img, [0, 0, 0], [rx - 2, ry - 1], [rx - 2, ry + 1])
                pygame.draw.line(self.img, [0, 0, 0], [rx + 2, ry - 1], [rx + 2, ry + 1])
                pygame.draw.rect(self.img, [255, 255, 255], [rx - 1, ry - 1, 3, 3])
                text = self.input_comps[i].name if t == 0 else self.output_comps[i].name
                if x < 0:
                    pygame.draw.line(self.img, [0, 0, 0], [rx + 3, ry], [14, ry])
                    self.draw_text(self.img, text, [16, ry], 0, 1)
                else:
                    pygame.draw.line(self.img, [0, 0, 0], [rx - 3, ry], [self.full_size[0] - 14, ry])
                    self.draw_text(self.img, text, [self.full_size[0] - 16, ry], 2, 1)
        self.draw_text(self.img, self.name, [self.full_size[0] // 2, self.full_size[1] // 2], 1, 1)
        pygame.draw.rect(self.img_small, [255, 255, 255], [14, 0, 31, 31])
        pygame.draw.rect(self.img_small, [0, 0, 0], [14, 0, 31, 31], 1)
        self.draw_text(self.img_small, self.name, [29, 15], 1, 1)

    def calculate(self):
        for i, s in enumerate(self.input_comps):
            if s.state != self.input_vals[i]:
                s.switch()
                if len(s.outputs[0]) > 0:
                    s.outputs[0][0].update()
        for comp in self.components:
            comp.update()
        for wire in self.wires:
            wire.update()
        for i, b in enumerate(self.output_comps):
            b.update()
            self.output_vals[i] = b.state

    def copy(self):
        copied_comps, copied_wires = copy(self.components, self.wires)
        inputs, outputs = get_inputs_outputs(copied_comps)
        return IntegratedCircuit(self.name, inputs, outputs, copied_comps, copied_wires, self.pos, self.img,
                                 self.img_small)

    def draw_text(self, surface, text, pos, x_offset, y_offset):
        t = self.small_font.render(text, True, [0, 0, 0])
        real_pos = [pos[0] - t.get_size()[0] // 2 * x_offset, pos[1] - t.get_size()[1] // 2 * y_offset]
        surface.blit(t, real_pos)

    def get_image(self):
        return self.img


def copy(components, wires):
    dic = {}
    copied_comps = []
    copied_wires = []
    for comp in components:
        copied = comp.copy()
        dic[comp] = copied
        copied_comps.append(copied)
    for wire in wires:
        if wire.input in components and wire.output in components:
            copied = Wire(dic[wire.input], wire.input_num, dic[wire.output], wire.output_num)
            copied_wires.append(copied)
    return copied_comps, copied_wires


def center(components):
    min_x = components[0].pos[0]
    max_x = min_x
    min_y = components[0].pos[1]
    max_y = min_y
    for comp in components:
        if comp.pos[0] < min_x:
            min_x = comp.pos[0]
        elif comp.pos[0] > max_x:
            max_x = comp.pos[0]
        if comp.pos[1] < min_y:
            min_y = comp.pos[1]
        elif comp.pos[1] > max_y:
            max_y = comp.pos[1]
    center_pos = [(min_x + max_x) // 2, (min_y + max_y) // 2]
    transpose(components, [-center_pos[0], -center_pos[1]])


def transpose(components, offset):
    for comp in components:
        comp.pos = [comp.pos[0] + offset[0], comp.pos[1] + offset[1]]


def get_inputs_outputs(components):
    inputs = []
    outputs = []
    for comp in components:
        if isinstance(comp, Switch):
            inputs.append(comp)
        elif isinstance(comp, Bulb):
            outputs.append(comp)
    inputs.sort(key = lambda s: (s.pos[1], s.pos[0]))
    outputs.sort(key = lambda b: (b.pos[1], b.pos[0]))
    return inputs, outputs


def create_display_images():
    table = [[True, False, True, True, False, True, True, True, True, True, True, False, True, False, True, True],
             [True, False, False, False, True, True, True, False, True, True, True, True, True, False, True, True],
             [True, True, True, True, True, False, False, True, True, True, True, False, False, True, False, False],
             [False, False, True, True, True, True, True, False, True, True, True, True, False, True, True, True],
             [True, False, True, False, False, False, True, False, True, False, True, True, True, True, True, True],
             [True, True, False, True, True, True, True, True, True, True, True, True, False, True, False, False],
             [True, False, True, True, False, True, True, False, True, True, False, True, True, True, True, False]]
    points = [[19, 5], [39, 5], [19, 25], [39, 25], [19, 45], [39, 45]]
    lines = [[0, 1], [0, 2], [1, 3], [2, 3], [2, 4], [3, 5], [4, 5]]
    result = []
    for i in range(16):
        image = pygame.image.load(r'img\display.png')
        for n, l in enumerate(lines):
            if table[n][i]:
                pygame.draw.line(image, [255, 0, 0], points[l[0]], points[l[1]], 3)
        result.append(image)
    return result


display_images = create_display_images()
