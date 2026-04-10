def make_vertical(text):
    return "&#10;".join(list(text))

xml_content = """<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1000" pageHeight="600" background="#ffffff">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>"""

# Root Node
xml_content += '''
    <mxCell id="root_node" value="基于低交互蜜罐的恶意流量识别与防御系统" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#cce5ff;strokeColor=#336699;fontColor=#000000;fontSize=16;fontStyle=1" vertex="1" parent="1">
      <mxGeometry x="300" y="40" width="400" height="40" as="geometry"/>
    </mxCell>'''

modules = [
    ("系统首页", ["态势感知", "攻击趋势", "数据总览"]),
    ("蜜罐管理", ["节点部署", "协议模拟", "状态监控", "端口分配"]),
    ("匹配规则", ["自定义项", "威胁评级", "高危阻断", "规则库"]),
    ("流量日志", ["日志检索", "正则引擎", "AI Agent", "溯源定位"]),
    ("恶意IP", ["防火墙", "记录追踪", "解封控制", "黑白名单"]),
    ("系统维护", ["账号管理", "权限配置", "模块授权"])
]

start_x = 50
mod_w = 120
mod_spacing = 30
mod_y = 140

# Top horizontal line from root
xml_content += f'''
    <mxCell id="root_down" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;endArrow=none;" edge="1" parent="1" source="root_node">
      <mxGeometry relative="1" as="geometry">
        <mxPoint x="500" y="100" as="targetPoint"/>
      </mxGeometry>
    </mxCell>'''

# The long horizontal backbone line
xml_content += f'''
    <mxCell id="backbone" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;endArrow=none;" edge="1" parent="1">
      <mxGeometry relative="1" as="geometry">
        <mxPoint x="{start_x + mod_w/2}" y="100" as="sourcePoint"/>
        <mxPoint x="{start_x + 5*(mod_w+mod_spacing) + mod_w/2}" y="100" as="targetPoint"/>
      </mxGeometry>
    </mxCell>'''

cell_id = 100

for i, (mod_name, subs) in enumerate(modules):
    mx = start_x + i * (mod_w + mod_spacing)
    
    # Module Box
    mod_id = f"mod_{i}"
    xml_content += f'''
    <mxCell id="{mod_id}" value="{mod_name}" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#cce5ff;strokeColor=#336699;fontColor=#000000;fontSize=14;fontStyle=1" vertex="1" parent="1">
      <mxGeometry x="{mx}" y="{mod_y}" width="{mod_w}" height="30" as="geometry"/>
    </mxCell>'''
    
    # Line from backbone to module
    xml_content += f'''
    <mxCell id="edge_{mod_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;endArrow=none;" edge="1" parent="1">
      <mxGeometry relative="1" as="geometry">
        <mxPoint x="{mx + mod_w/2}" y="100" as="sourcePoint"/>
        <mxPoint x="{mx + mod_w/2}" y="{mod_y}" as="targetPoint"/>
      </mxGeometry>
    </mxCell>'''
    
    # Line under module to sub-functions backbone
    sub_backbone_y = mod_y + 50
    xml_content += f'''
    <mxCell id="down_{mod_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;endArrow=none;" edge="1" parent="1">
      <mxGeometry relative="1" as="geometry">
        <mxPoint x="{mx + mod_w/2}" y="{mod_y+30}" as="sourcePoint"/>
        <mxPoint x="{mx + mod_w/2}" y="{sub_backbone_y}" as="targetPoint"/>
      </mxGeometry>
    </mxCell>'''
    
    # Sub-functions
    sub_w = 20
    sub_h = 160
    sub_spacing = 8
    total_sub_w = len(subs) * sub_w + (len(subs)-1) * sub_spacing
    sub_start_x = mx + (mod_w - total_sub_w) / 2
    
    # Sub-functions backbone horizontal 
    xml_content += f'''
    <mxCell id="sub_back_{mod_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;endArrow=none;" edge="1" parent="1">
      <mxGeometry relative="1" as="geometry">
        <mxPoint x="{sub_start_x + sub_w/2}" y="{sub_backbone_y}" as="sourcePoint"/>
        <mxPoint x="{sub_start_x + total_sub_w - sub_w/2}" y="{sub_backbone_y}" as="targetPoint"/>
      </mxGeometry>
    </mxCell>'''
    
    for j, sub in enumerate(subs):
        sx = sub_start_x + j * (sub_w + sub_spacing)
        sy = sub_backbone_y + 20
        
        # Connection down to sub
        xml_content += f'''
        <mxCell id="edge_sub_{cell_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;strokeColor=#333333;endArrow=none;" edge="1" parent="1">
          <mxGeometry relative="1" as="geometry">
            <mxPoint x="{sx + sub_w/2}" y="{sub_backbone_y}" as="sourcePoint"/>
            <mxPoint x="{sx + sub_w/2}" y="{sy}" as="targetPoint"/>
          </mxGeometry>
        </mxCell>'''
        
        # Format text vertically
        if sub == "AI Agent":
            # Hardcode vertical text for English mixed
            v_text = "A&#10;I&#10; &#10;A&#10;g&#10;e&#10;n&#10;t"
            sub_h_local = 160
        else:
            v_text = make_vertical(sub)
            sub_h_local = 120
            
        xml_content += f'''
        <mxCell id="sub_{cell_id}" value="{v_text}" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#e6f2ff;strokeColor=#6699cc;fontColor=#000000;fontSize=12;" vertex="1" parent="1">
          <mxGeometry x="{sx}" y="{sy}" width="{sub_w}" height="{sub_h_local}" as="geometry"/>
        </mxCell>'''
        cell_id += 1

xml_content += '''
  </root>
</mxGraphModel>'''

with open('e:/桌面/zuoye/毕业设计/src/backend/func_diagram.py.xml', 'w', encoding='utf-8') as f:
    f.write(xml_content)
