import math
import pygame
import components as comps
import json

SCREEN_SIZE = [1600, 900]
SCREEN = pygame.display.set_mode(SCREEN_SIZE)
running = True
scroll = [0, 0]
scroll_prev = [0, 0]
mouse_start = [0, 0]
components = []
table = []
integrated = {}
wires = []
mouse = 'up'
keys = {pygame.K_LSHIFT: 'up', pygame.K_c: 'up', pygame.K_v: 'up', pygame.K_DELETE: 'up', pygame.K_n: 'up',
        pygame.K_m: 'up', pygame.K_s: 'up', pygame.K_l: 'up', pygame.K_u: 'up'}
mouse_type = ''
mouse_offsets = []
selection_rect = [0, 0, 0, 0]
selected = []
selected_wires = []
wire_comp = None
wire_num = 0
max_scroll_dist = 0
clipboard_comps = []
clipboard_wires = []
typing = False
text = ''
text_limit = 2
pygame.font.init()
font = pygame.font.Font(None, 32)
page = 0
buttons = pygame.image.load(r'img\buttons.png')


def main():
    global font
    pygame.init()
    refill_table()
    while running:
        update()
        check_events()
        handle_mouse()
        draw()
    pygame.quit()


def update():
    for comp in components:
        comp.update()
    for wire in wires:
        wire.update()


def check_events():
    global running, mouse, keys, text
    left = pygame.mouse.get_pressed()[0]
    if left and mouse == 'just_down':
        mouse = 'down'
    elif not left and mouse == 'just_up':
        mouse = 'up'
    for key, val in keys.items():
        if val == 'just_down' and pygame.key.get_pressed()[key]:
            keys[key] = 'down'
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if pygame.mouse.get_pressed()[0]:
                mouse = 'just_down'
        elif event.type == pygame.MOUSEBUTTONUP:
            if not pygame.mouse.get_pressed()[0]:
                mouse = 'just_up'
        elif event.type == pygame.KEYDOWN:
            if event.key in keys:
                keys[event.key] = 'just_down'
            if typing:
                if event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif event.key == pygame.K_RETURN:
                    end_typing()
                else:
                    if len(text) < text_limit:
                        text += event.unicode
        elif event.type == pygame.KEYUP:
            if event.key in keys:
                keys[event.key] = 'up'


def handle_mouse():
    global mouse_start, scroll_prev, mouse_type, selected, mouse_offsets, wire_comp, wire_num, wires, selection_rect, \
        max_scroll_dist, clipboard_comps, clipboard_wires
    if typing:
        return
    pos = pygame.mouse.get_pos()
    if mouse == 'just_down':
        if pos[0] < 300:
            if keys[pygame.K_LSHIFT] == 'up':
                check_table(pos)
            return
        if keys[pygame.K_LSHIFT] == 'down' or keys[pygame.K_LSHIFT] == 'just_down':
            start_selecting(pos)
            return
        if check_components(pos):
            return
        wire = check_wires(pos)
        mouse_type = 'scroll_w' if wire else 'scroll'
        mouse_start = pos
        max_scroll_dist = 0
    elif mouse == 'down':
        if mouse_type == 'move_new':
            move_selected(pos)
        if mouse_type == 'selection':
            select(pos)
        elif mouse_type == 'switch':
            if (mouse_start[0] - pos[0]) ** 2 + (mouse_start[1] - pos[1]) ** 2 > 9:
                mouse_type = 'move'
        elif mouse_type == 'move':
            move_selected(pos)
        elif mouse_type == 'scroll' or mouse_type == 'scroll_w':
            change_scroll(pos)
            if keys[pygame.K_LSHIFT] == 'just_down':
                end_scroll()
                start_selecting(pos)
    elif mouse == 'just_up':
        if mouse_type == 'connect_in' or mouse_type == 'connect_out':
            connect(pos)
        elif mouse_type == 'switch':
            switch(pos)
        elif mouse_type == 'move_new':
            add_new(pos)
        elif mouse_type == 'move':
            move_selected(pos)
            turn_off_button()
            if pos[0] < 300:
                delete_selected()
        elif mouse_type == 'scroll' or mouse_type == 'scroll_w':
            change_scroll(pos)
            end_scroll()
            if max_scroll_dist < 9 and mouse_type != 'scroll_w':
                selected.clear()
                selected_wires.clear()
        mouse_type = ''
    else:
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_c] == 'just_down':
            copy()
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_v] == 'just_down':
            paste(pos)
        if keys[pygame.K_DELETE] == 'just_down':
            delete_selected()
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_n] == 'just_down':
            if len(selected) == 1 and (isinstance(selected[0], comps.Switch) or isinstance(selected[0], comps.Bulb)):
                start_typing(False)
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_m] == 'just_down':
            start_typing(True)
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_s] == 'just_down':
            save()
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_l] == 'just_down':
            load()
        if pygame.key.get_pressed()[pygame.K_LCTRL] and keys[pygame.K_u] == 'just_down':
            unpack()


def draw():
    pygame.draw.rect(SCREEN, [80, 80, 80], [300, 0, SCREEN_SIZE[0], SCREEN_SIZE[1]])
    x_start = (scroll[0] - SCREEN_SIZE[0] // 2 + 300) // 50 * 50
    y_start = (scroll[1] - SCREEN_SIZE[1] // 2) // 50 * 50
    x_end = scroll[0] + SCREEN_SIZE[0] // 2
    y_end = scroll[1] + SCREEN_SIZE[1] // 2
    for i in range(x_start, x_end, 50):
        x = get_pos([i, 0])[0]
        pygame.draw.line(SCREEN, [100, 100, 100], [x, 0], [x, SCREEN_SIZE[1]])
    for i in range(y_start, y_end, 50):
        y = get_pos([0, i])[1]
        pygame.draw.line(SCREEN, [100, 100, 100], [0, y], [SCREEN_SIZE[0], y])
    for comp in reversed(components):
        image = comp.get_image()
        SCREEN.blit(image, get_rect(comp.pos, comp.full_size))
    for wire in wires:
        pos_a = get_pos(wire.start_pos())
        pos_b = get_pos(wire.end_pos())
        if wire in selected_wires:
            pygame.draw.line(SCREEN, [0, 150, 200], pos_a, pos_b, 3)
        color = [200, 0, 0] if wire.state else [0, 0, 0]
        pygame.draw.line(SCREEN, color, pos_a, pos_b)
    pos = pygame.mouse.get_pos()
    if mouse_type == 'selection':
        draw_translucent_rect(selection_rect, [0, 150, 200], 64)
        pygame.draw.rect(SCREEN, [0, 150, 200], selection_rect, 1)
    elif mouse_type == 'connect_in' or mouse_type == 'connect_out':
        pygame.draw.line(SCREEN, [0, 0, 0], mouse_start, pos)
    pygame.draw.rect(SCREEN, [50, 50, 50], [0, 0, 300, SCREEN_SIZE[1]])
    pygame.draw.line(SCREEN, [0, 0, 0], [300, 0], [300, SCREEN_SIZE[1]])
    for comp in table:
        if (isinstance(comp, comps.IntegratedCircuit) or isinstance(comp, comps.FlipFlop)) and comp not in selected:
            image = comp.img_small
        else:
            image = comp.get_image()
        rect = get_rect(comp.pos, image.get_size(), comp in selected)
        SCREEN.blit(image, rect)
        SCREEN.blit(buttons, [0, SCREEN_SIZE[1] - 50, 300, 50])
    for comp in selected:
        rect = get_rect(comp.pos, comp.full_size, True)
        draw_translucent_rect(rect, [0, 150, 200], 64)
    if typing:
        draw_translucent_rect([300, 0, SCREEN_SIZE[0] - 300, SCREEN_SIZE[1]], [0, 0, 0], 64)
        pygame.draw.rect(SCREEN, [255, 255, 255], [310, SCREEN_SIZE[1] - 50, SCREEN_SIZE[0] - 320, 40])
        t = font.render(text, True, [0, 0, 0])
        SCREEN.blit(t, [315, SCREEN_SIZE[1] - 30 - t.get_size()[1] // 2])
    pygame.display.update()


def check_table(pos):
    global mouse_type, page
    left = pygame.Rect(125, SCREEN_SIZE[1] - 50, 50, 50)
    right = pygame.Rect(225, SCREEN_SIZE[1] - 50, 50, 50)
    if left.collidepoint(pos[0], pos[1]):
        if page > 0:
            page -= 1
            refill_table()
    elif right.collidepoint(pos[0], pos[1]):
        if page < (len(integrated) - 1) // 30:
            page += 1
            refill_table()
    for comp in table:
        if isinstance(comp, comps.IntegratedCircuit):
            rect = pygame.Rect(get_rect(comp.pos, [59, 31], False))
        else:
            rect = pygame.Rect(get_rect(comp.pos, comp.size, False))
        if rect.collidepoint(pos[0], pos[1]):
            mouse_type = 'move_new'
            selected.clear()
            selected.append(comp)
            mouse_offsets.clear()
            mouse_offsets.append([rect.centerx - pos[0], rect.centery - pos[1]])
            move_selected(pos)
            return


def start_selecting(pos):
    global mouse_start, mouse_type
    mouse_start = pos
    mouse_type = 'selection'
    if not pygame.key.get_pressed()[pygame.K_LCTRL]:
        selected.clear()
        selected_wires.clear()


def check_components(pos):
    global mouse_type, wire_comp, wire_num, mouse_start
    for comp in components:
        rect = pygame.Rect(get_rect(comp.pos, comp.full_size, True, True))
        if rect.collidepoint(pos[0], pos[1]):
            for t, array in enumerate([comp.inputs, comp.outputs]):
                for i, dot in enumerate(array):
                    if t == 1 or dot is None:
                        offset = comp.input_offsets[i] if t == 0 else comp.output_offsets[i]
                        dot_pos = [comp.pos[0] + offset[0], comp.pos[1] + offset[1]]
                        dot_rect = pygame.Rect(get_rect(dot_pos, [11, 11]))
                        if dot_rect.collidepoint(pos[0], pos[1]):
                            mouse_type = 'connect_in' if t == 0 else 'connect_out'
                            wire_comp = comp
                            wire_num = i
                            mouse_start = [dot_rect.centerx, dot_rect.centery]
                            return True
            rect = pygame.Rect(get_rect(comp.pos, comp.size))
            if rect.collidepoint(pos[0], pos[1]):
                if isinstance(comp, comps.Button):
                    comp.set_state(True)
                mouse_type = 'switch' if isinstance(comp, comps.Switch) else 'move'
                mouse_start = pos
                if comp in selected:
                    mouse_offsets.clear()
                    for sel in selected:
                        sel_rect = pygame.Rect(get_rect(sel.pos, sel.size))
                        mouse_offsets.append([sel_rect.centerx - pos[0], sel_rect.centery - pos[1]])
                else:
                    selected.clear()
                    selected.append(comp)
                    mouse_offsets.clear()
                    mouse_offsets.append([rect.centerx - pos[0], rect.centery - pos[1]])
                    selected_wires.clear()
                return True
    return False


def check_wires(pos):
    min_dist = 6
    chosen = None
    for wire in wires:
        rel_pos = get_pos_mouse(pos)
        dist = point_line_dist(wire.start_pos(), wire.end_pos(), rel_pos)
        if dist < min_dist:
            chosen = wire
            min_dist = dist
    if chosen is not None and chosen not in selected_wires:
        selected.clear()
        selected_wires.clear()
        selected_wires.append(chosen)
    if chosen is None:
        return False
    return True


def move_selected(pos):
    for i, sel in enumerate(selected):
        sel.pos = get_pos_mouse(pos)
        sel.pos[0] += mouse_offsets[i][0]
        sel.pos[1] += mouse_offsets[i][1]
        if pygame.key.get_pressed()[pygame.K_q]:
            sel.pos[0] = sel.pos[0] // 15 * 15 + 7
            sel.pos[1] = sel.pos[1] // 15 * 15 + 7


def select(pos):
    global selection_rect
    x_min = min(mouse_start[0], pos[0])
    width = abs(mouse_start[0] - pos[0])
    y_min = min(mouse_start[1], pos[1])
    height = abs(mouse_start[1] - pos[1])
    selection_rect = [x_min, y_min, width, height]
    for comp in components:
        if comp not in selected:
            rect = pygame.Rect(get_rect(comp.pos, comp.size))
            if rect.colliderect(pygame.Rect(selection_rect)):
                selected.append(comp)
    for sel in selected:
        for arr in sel.outputs:
            for wire in arr:
                if wire not in selected_wires and wire.output in selected:
                    selected_wires.append(wire)


def change_scroll(pos):
    global scroll, max_scroll_dist
    scroll[0] = scroll_prev[0] + mouse_start[0] - pos[0]
    scroll[1] = scroll_prev[1] + mouse_start[1] - pos[1]
    dist = (scroll_prev[0] - scroll[0]) ** 2 + (scroll_prev[1] - scroll[1]) ** 2
    if dist > max_scroll_dist:
        max_scroll_dist = dist


def connect(pos):
    if pos[0] > 300:
        for comp in components:
            array = comp.outputs if mouse_type == 'connect_in' else comp.inputs
            offsets = comp.output_offsets if mouse_type == 'connect_in' else comp.input_offsets
            for i, dot in enumerate(array):
                if mouse_type == 'connect_in' or dot is None:
                    dot_pos = [comp.pos[0] + offsets[i][0], comp.pos[1] + offsets[i][1]]
                    dot_rect = pygame.Rect(get_rect(dot_pos, [11, 11]))
                    if dot_rect.collidepoint(pos[0], pos[1]):
                        if mouse_type == 'connect_out':
                            wires.append(comps.Wire(wire_comp, wire_num, comp, i))
                        else:
                            wires.append(comps.Wire(comp, i, wire_comp, wire_num))
                        selected_wires.clear()
                        selected_wires.append(wires[-1])
                        selected.clear()


def switch(pos):
    if len(selected) > 1:
        for sel in selected:
            if isinstance(sel, comps.Switch):
                sel_rect = pygame.Rect(get_rect(sel.pos, sel.size))
                if sel_rect.collidepoint(pos):
                    sel.switch()
                    selected.clear()
                    selected.append(sel)
                    mouse_offsets.clear()
                    break
    else:
        selected[0].switch()
    selected_wires.clear()


def turn_off_button():
    for sel in selected:
        if isinstance(sel, comps.Button):
            sel.set_state(False)


def add_new(pos):
    move_selected(pos)
    if pos[0] > 300:
        components.append(selected[0])
    else:
        rect = pygame.Rect(25, SCREEN_SIZE[1] - 50, 50, 50)
        if isinstance(selected[0], comps.IntegratedCircuit) and rect.collidepoint(pos[0], pos[1]):
            delete_integrated(selected[0].name)
        selected.clear()
    refill_table()


def end_scroll():
    scroll_prev[0] = scroll[0]
    scroll_prev[1] = scroll[1]


def delete_selected():
    delete_comps(selected_wires)
    selected_wires.clear()
    delete_comps(selected)
    selected.clear()


def copy():
    global clipboard_comps, clipboard_wires
    if len(selected) > 0:
        clipboard_comps, clipboard_wires = comps.copy(selected, selected_wires)
        comps.center(clipboard_comps)


def paste(pos):
    global selected, selected_wires
    if len(clipboard_comps) > 0:
        copied_comps, copied_wires = comps.copy(clipboard_comps, clipboard_wires)
        comps.transpose(copied_comps, get_pos_mouse(pos))
        components.extend(copied_comps)
        wires.extend(copied_wires)
        selected = copied_comps
        selected_wires = copied_wires


def unpack():
    global clipboard_comps, clipboard_wires
    if len(selected) == 1 and isinstance(selected[0], comps.IntegratedCircuit):
        clipboard_comps, clipboard_wires = comps.copy(selected[0].components, selected[0].wires)
        comps.center(clipboard_comps)


def create_component(name):
    if len(selected) > 0:
        copied_comps, copied_wires = comps.copy(selected, selected_wires)
        comps.center(copied_comps)
        inputs, outputs = comps.get_inputs_outputs(copied_comps)
        integrated[name] = comps.IntegratedCircuit(name, inputs, outputs, copied_comps, copied_wires, [0, 0])
        pygame.image.save(integrated[name].img, r'img\result.png')
        refill_table()


def delete_integrated(name):
    selected.clear()
    selected_wires.clear()
    integrated.pop(name)
    to_delete = []
    for comp in components:
        if isinstance(comp, comps.IntegratedCircuit) and comp.name == name:
            to_delete.append(comp)
    delete_comps(to_delete)
    to_delete = []
    for key, val in integrated.items():
        for comp in val.components:
            if isinstance(comp, comps.IntegratedCircuit) and comp.name == name:
                to_delete.append(key)
    for inte in to_delete:
        delete_integrated(inte)


def save():
    result = {'integrated': [], 'content': {}}
    for inte in integrated.values():
        result['integrated'].append({'name': inte.name, 'content': get_json(inte.components, inte.wires)})
    result['content'] = get_json(components, wires)
    with open('save.txt', 'w') as file:
        file.write(json.dumps(result))


def load():
    global components, wires, selected, selected_wires
    with open('save.txt', 'r') as file:
        content = json.loads(file.read())
        components.clear()
        wires.clear()
        selected.clear()
        selected_wires.clear()
        integrated.clear()
        for inte in content['integrated']:
            selected, selected_wires = get_comps(inte['content'])
            create_component(inte['name'])
        selected.clear()
        selected_wires.clear()
        components, wires = get_comps(content['content'])
        return


def get_json(comp_arr, wire_arr):
    result = {'components': [], 'wires': []}
    dic = {}
    for i, comp in enumerate(comp_arr):
        comp_j = {'type': str(type(comp)).split('.')[1][:-2], 'name': comp.name, 'id': i, 'pos': comp.pos}
        dic[comp] = i
        result['components'].append(comp_j)
    for wire in wire_arr:
        wire_j = {'start': dic[wire.input], 'start_num': wire.input_num, 'end': dic[wire.output],
                  'end_num': wire.output_num}
        result['wires'].append(wire_j)
    return result


def get_comps(json_content):
    comp_arr = []
    wire_arr = []
    for comp_j in json_content['components']:
        comp_type = getattr(comps, comp_j['type'])
        if comp_type is comps.IntegratedCircuit:
            comp = integrated[comp_j['name']].copy()
            comp.pos = comp_j['pos']
        else:
            comp = comp_type(comp_j['name'], comp_j['pos'])
        comp_arr.append(comp)
    for wire in json_content['wires']:
        wire_arr.append(comps.Wire(comp_arr[wire['start']], wire['start_num'], comp_arr[wire['end']], wire['end_num']))
    return comp_arr, wire_arr


def start_typing(long):
    global typing, text, text_limit
    typing = True
    text = '' if long else selected[0].name
    text_limit = 3 if long else 2


def end_typing():
    global typing
    typing = False
    if text_limit == 2:
        selected[0].name = text
    else:
        if text in integrated:
            start_typing(True)
        else:
            create_component(text)


def draw_translucent_rect(rect, color, alpha):
    s = pygame.Surface(rect[2:])
    s.set_alpha(alpha)
    s.fill(color)
    SCREEN.blit(s, rect[:2])


def delete_comps(comp):
    for c in comp:
        if isinstance(c, comps.Component):
            all_wires = c.outputs
            all_wires.append(c.inputs)
            for array in all_wires:
                counter = 0
                while counter < len(array):
                    if array[counter] is not None:
                        wires.remove(array[counter])
                        array[counter].delete()
                    else:
                        counter += 1
            components.remove(c)
        else:
            wires.remove(c)
            c.delete()


def point_line_dist(a, b, p):
    ab = [b[0] - a[0], b[1] - a[1]]
    bp = [p[0] - b[0], p[1] - b[1]]
    ap = [p[0] - a[0], p[1] - a[1]]
    ab_bp = ab[0] * bp[0] + ab[1] * bp[1]
    ab_ap = ab[0] * ap[0] + ab[1] * ap[1]
    if ab_bp > 0:
        return math.sqrt((p[1] - b[1]) ** 2 + (p[0] - b[0]) ** 2)
    if ab_ap < 0:
        return math.sqrt((p[1] - a[1]) ** 2 + (p[0] - a[0]) ** 2)
    num = abs((b[0] - a[0]) * (a[1] - p[1]) - (a[0] - p[0]) * (b[1] - a[1]))
    den = math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2)
    return num / den


def get_rect(pos, size, relative = True, big = False):
    if big:
        size = [size[0] + 10, size[1]]
    if relative:
        x = pos[0] + SCREEN_SIZE[0] // 2 - scroll[0] - size[0] // 2
        y = pos[1] + SCREEN_SIZE[1] // 2 - scroll[1] - size[1] // 2
        return [x, y, size[0], size[1]]
    return [pos[0] - size[0] // 2, pos[1] - size[1] // 2 - 1, size[0], size[1]]


def get_pos(pos):
    x = pos[0] + SCREEN_SIZE[0] // 2 - scroll[0]
    y = pos[1] + SCREEN_SIZE[1] // 2 - scroll[1]
    return [x, y]


def get_pos_mouse(pos):
    x = pos[0] - SCREEN_SIZE[0] // 2 + scroll[0]
    y = pos[1] - SCREEN_SIZE[1] // 2 + scroll[1]
    return [x, y]


def refill_table():
    global table
    table = [comps.Switch('', [50, 50]), comps.Button('', [150, 50]), comps.Bulb('', [50, 100]),
             comps.Display('', [150, 100]), comps.Gate('buffer', [50, 150]), comps.Gate('not', [150, 150]),
             comps.Gate('and', [250, 150]), comps.Gate('nand', [50, 200]), comps.Gate('or', [150, 200]),
             comps.Gate('nor', [250, 200]), comps.Gate('xor', [50, 250]), comps.Gate('xnor', [150, 250]),
             comps.FlipFlop('sr', [250, 250]), comps.FlipFlop('jk', [50, 300]), comps.FlipFlop('d', [150, 300]),
             comps.FlipFlop('t', [250, 300])]
    for i, inte in enumerate(list(integrated.values())[(page * 30):(page * 30 + 30)]):
        comp = inte.copy()
        comp.pos = [i % 3 * 100 + 50, 350 + i % 30 // 3 * 50]
        table.append(comp)


if __name__ == '__main__':
    main()
