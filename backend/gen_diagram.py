xml_content = """<mxGraphModel dx="1000" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" background="#ffffff">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>"""

layers = [
    ('访问层', '管理员 / 黑客 (Client/Browser)', '#e0e0e0', '#333333', 40, 80),
    ('前端UI层', 'Vue.js 3 + Element Plus\\n(数据大屏 / 系统管理面板)', '#a9dfbf', '#1e8449', 140, 80),
    ('交互服务层', 'Flask RESTful API', '#aed6f1', '#2874a6', 240, 80),
    ('核心业务层', '', '#f3c68f', '#b9770e', 340, 160),
    ('数据层', 'MySQL\\n(日志表、规则表、蜜罐配置、IP库)', '#f1948a', '#b03a2e', 520, 80),
    ('运行环境', 'Python 3 + 大语言模型 (LLM) 环境', '#f5b7b1', '#a93226', 620, 80)
]

cell_id = 2

for i, (title, content, bg, border, y, h) in enumerate(layers):
    # Left title block
    xml_content += f'''
    <mxCell id="{cell_id}" value="{title}" style="rounded=0;whiteSpace=wrap;html=1;fillColor={bg};strokeColor={border};fontColor=#000000;fontStyle=1" vertex="1" parent="1">
      <mxGeometry x="40" y="{y}" width="100" height="{h}" as="geometry"/>
    </mxCell>'''
    cell_id += 1
    
    # Right content block background
    xml_content += f'''
    <mxCell id="{cell_id}" value="{content}" style="rounded=0;whiteSpace=wrap;html=1;fillColor={bg};strokeColor={border};fontColor=#000000;fontSize=16;fontStyle=1" vertex="1" parent="1">
      <mxGeometry x="160" y="{y}" width="600" height="{h}" as="geometry"/>
    </mxCell>'''
    cell_id += 1
    
    # Dash lines between layers
    if i > 0:
        prev_y = y - 10
        xml_content += f'''
        <mxCell id="{cell_id}" value="" style="endArrow=none;dashed=1;html=1;strokeWidth=2;strokeColor=#999999;" edge="1" parent="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="30" y="{prev_y}" as="sourcePoint"/>
            <mxPoint x="780" y="{prev_y}" as="targetPoint"/>
          </mxGeometry>
        </mxCell>'''
        cell_id += 1
        
        # Double arrows between content blocks
        xml_content += f'''
        <mxCell id="{cell_id}" value="" style="shape=flexArrow;endArrow=classic;startArrow=classic;html=1;fillColor=#ffffff;strokeColor=#000000;width=10;endSize=5.33;startSize=5.33" edge="1" parent="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="260" y="{y}" as="sourcePoint"/>
            <mxPoint x="260" y="{y-20}" as="targetPoint"/>
          </mxGeometry>
        </mxCell>'''
        cell_id += 1
        
        xml_content += f'''
        <mxCell id="{cell_id}" value="" style="shape=flexArrow;endArrow=classic;startArrow=classic;html=1;fillColor=#ffffff;strokeColor=#000000;width=10;endSize=5.33;startSize=5.33" edge="1" parent="1">
          <mxGeometry width="50" height="50" relative="1" as="geometry">
            <mxPoint x="660" y="{y}" as="sourcePoint"/>
            <mxPoint x="660" y="{y-20}" as="targetPoint"/>
          </mxGeometry>
        </mxCell>'''
        cell_id += 1

# Add smaller boxes inside backend (row 4)
backend_modules = [
    ('低交互蜜罐引擎\\n(流量引流/协议模拟)', 180, 360, 260, 50),
    ('流量捕获与解析\\n(数据预处理)', 480, 360, 260, 50),
    ('强规则检测引擎\\n(高危特征正则)', 180, 430, 260, 50),
    ('AI大模型检测引擎\\n(未知威胁/行为判定)', 480, 430, 260, 50)
]

for title, x, y, w, h in backend_modules:
    xml_content += f'''
    <mxCell id="{cell_id}" value="{title}" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=#b9770e;fontColor=#000000;fontStyle=1" vertex="1" parent="1">
      <mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/>
    </mxCell>'''
    cell_id += 1

xml_content += '''
  </root>
</mxGraphModel>'''

with open('e:/桌面/zuoye/毕业设计/src/backend/system_arch.xml', 'w', encoding='utf-8') as f:
    f.write(xml_content)
