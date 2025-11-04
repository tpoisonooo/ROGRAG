import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from typing import List
import gradio as gr
from loguru import logger

# 导入API客户端
from huixiangdou.client.api_client import HuixiangDouAPIClient

# 设置环境变量，改变 Gradio 的默认临时目录
os.environ["GRADIO_TEMP_DIR"] = "gradio_temp"

def ymd():
    """获取当前日期并创建日期目录"""
    now = datetime.now()
    date_string = now.strftime("%Y-%m-%d")
    os.makedirs(date_string, exist_ok=True)
    return date_string


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='HuixiangDou Gradio UI - API Client Mode')
    parser.add_argument('--server_url',
                        type=str,
                        default='http://localhost:23333',
                        help='HuixiangDou服务器URL，默认为 http://localhost:23333')
    parser.add_argument('--placeholder',
                        type=str,
                        default='百草园里有什么？',
                        help='用户查询的占位符文本')
    parser.add_argument('--theme',
                        type=str,
                        default='soft',
                        help='Gradio主题，默认为 `soft`')
    parser.add_argument('--server_port',
                        type=int,
                        default=8888,
                        help='Gradio服务器端口，默认为 8888')
    parser.add_argument('--share',
                        action='store_true',
                        default=False,
                        help='是否创建共享链接')
    
    args = parser.parse_args()
    return args


# 全局变量
main_args = None
language = 'zh_cn'
enable_web_search = False
current_db_name = 'HuixiangDou'  # 当前数据库名称
server_base_url = 'http://localhost:23333'


def on_language_changed(value: str):
    """处理语言切换"""
    global language
    language = value
    return f'已切换到 {value}'


def on_web_search_changed(value: str):
    """处理网络搜索开关"""
    global enable_web_search
    if 'no' in value.lower():
        enable_web_search = False
    else:
        enable_web_search = True
    return f'网络搜索设置为 {enable_web_search}'


def on_db_name_changed(value: str):
    """处理数据库名称变化"""
    global current_db_name
    
    if not value or value.strip() == '':
        return f'数据库名称不能为空'
    
    value = value.strip()
    if value != current_db_name:
        current_db_name = value
        logger.info(f'Switched database to: {current_db_name}')
        return f'已切换到数据库: {current_db_name}'
    return f'当前数据库: {current_db_name}'


def format_refs(refs: List[dict]) -> str:
    """格式化参考资料"""
    if not refs:
        return ''
    
    text = ''
    if language == 'zh_cn':
        text += '**参考资料：**\r\n'
    else:
        text += '**References:**\r\n'
    
    seen = set()
    for ref in refs:
        source = ref.get('source_or_url', '')
        if source and source not in seen:
            seen.add(source)
            text += f'* {source}\r\n'
    
    text += '\r\n'
    return text


async def get_files_list(db_name: str = None) -> str:
    """获取文件列表"""
    try:
        async with HuixiangDouAPIClient(server_base_url) as client:
            files = await client.list_files(db_name or current_db_name)
            if files:
                return '\n'.join(files)
            else:
                return '知识库为空' if language == 'zh_cn' else 'Knowledge base is empty'
    except Exception as e:
        logger.error(f"获取文件列表失败: {e}")
        return f'获取文件列表失败: {str(e)}'


async def get_databases_list() -> List[str]:
    """获取数据库列表"""
    try:
        async with HuixiangDouAPIClient(server_base_url) as client:
            databases = await client.list_databases()
            return databases
    except Exception as e:
        logger.error(f"获取数据库列表失败: {e}")
        return [current_db_name]  # 返回当前数据库作为备选


async def add_files(files: List, progress=gr.Progress()):
    """添加文件到知识库"""
    if not files:
        status_msg = '没有上传任何文件' if language == 'zh_cn' else 'No files uploaded'
        files_list = await get_files_list()
        return status_msg, files_list
    
    # 转换Gradio文件对象为文件路径
    file_paths = []
    for file in files:
        if hasattr(file, 'name'):
            file_paths.append(file.name)
        else:
            file_paths.append(str(file))
    
    logger.info(f"准备添加文件: {file_paths} 到数据库: {current_db_name}")
    
    try:
        async with HuixiangDouAPIClient(server_base_url) as client:
            progress(0.1, desc="准备上传文件...")
            
            total_files = len(file_paths)
            current_file = 0
            
            async for progress_data in client.add_files(file_paths, current_db_name):
                if 'data' in progress_data:
                    data = progress_data['data']
                    progress_val = data.get('progress', 0)
                    message = data.get('message', '')
                    current_file = data.get('current_file', 0)
                    total_files = data.get('total_files', total_files)
                    
                    # 更新进度条
                    progress(progress_val, desc=f"{message}")
                    
                    # 如果完成，更新文件列表
                    if progress_val >= 1.0:
                        files_list = await get_files_list()
                        status_msg = f'扩展成功 (数据库: {current_db_name})'
                        return status_msg, files_list
            
            # 如果流结束但没有明确的完成信号
            files_list = await get_files_list()
            status_msg = f'扩展完成 (数据库: {current_db_name})'
            return status_msg, files_list
            
    except Exception as e:
        logger.error(f"添加文件失败: {e}")
        error_msg = f'扩展失败: {str(e)} (数据库: {current_db_name})'
        files_list = await get_files_list()
        return error_msg, files_list


async def drop_db():
    """清空数据库"""
    try:
        async with HuixiangDouAPIClient(server_base_url) as client:
            result = await client.drop_db(current_db_name)
            files_list = await get_files_list()
            status_msg = f'删除成功 (数据库: {current_db_name})'
            return status_msg, files_list
    except Exception as e:
        logger.error(f"清空数据库失败: {e}")
        files_list = await get_files_list()
        error_msg = f'删除失败: {str(e)} (数据库: {current_db_name})'
        return error_msg, files_list


async def predict(text: str, history: List):
    """预测/聊天功能"""
    if not text:
        text = main_args.placeholder
    
    logger.info(f"用户问题: {text} (数据库: {current_db_name})")
    
    try:
        async with HuixiangDouAPIClient(server_base_url) as client:
            full_response = ""
            refs_text = ""
            
            async for response_text in client.chat(
                text=text,
                language=language,
                enable_web_search=enable_web_search,
                db_name=current_db_name,
                history=history
            ):
                full_response = response_text
                
                # 检查是否有参考资料（在完整响应中）
                if '**参考资料：**' in response_text or '**References:**' in response_text:
                    # 参考资料已经包含在响应中
                    yield full_response
                else:
                    # 只显示主要回复内容
                    yield full_response
            
            logger.info(f"完整回复: {len(full_response)} 字符")
            
    except Exception as e:
        logger.error(f"聊天失败: {e}")
        error_msg = f"抱歉，聊天服务暂时不可用: {str(e)}"
        if language == 'zh_cn':
            error_msg = f"抱歉，聊天服务暂时不可用: {str(e)}"
        else:
            error_msg = f"Sorry, chat service is temporarily unavailable: {str(e)}"
        yield error_msg


async def refresh_files_list():
    """刷新文件列表"""
    try:
        files_list = await get_files_list()
        return files_list
    except Exception as e:
        logger.error(f"刷新文件列表失败: {e}")
        return f'刷新失败: {str(e)}'


async def export_graph_data():
    """导出图谱数据"""
    try:
        async with HuixiangDouAPIClient(server_base_url) as client:
            result = await client.export_graph(current_db_name)
            
            if result.get('status', {}).get('code') == 0:
                data = result.get('data', {})
                download_token = data.get('download_url', '').split('/')[-1]
                message = f"""
**图谱导出成功！**\n\n
📊 **导出信息：**\n
- 数据库: {data.get('db_name', current_db_name)}\n
- 文件大小: {data.get('file_size', 0):,} 字节\n
- 下载令牌: `{download_token}`\n
- 导出路径: {data.get('export_path', 'Unknown')}\n\n
**下一步：**\n
在下方输入框中已自动填入下载令牌，点击下载按钮即可获取文件。
                """
                # 返回消息和自动填充的下载令牌
                return message, download_token
            else:
                error_msg = result.get('status', {}).get('error', '导出失败')
                return f"**导出失败:** {error_msg}", ""
                
    except Exception as e:
        logger.error(f"导出图谱失败: {e}")
        return f"**导出失败:** {str(e)}", ""


async def download_export_file(download_token: str):
    """下载导出文件 - 直接返回下载链接，让浏览器下载到本地"""
    if not download_token:
        return "请提供下载令牌", gr.update(visible=False), gr.update(visible=False)
    
    try:
        # 构建直接下载URL
        download_url = f"{server_base_url}/v2/download_export/{download_token}"
        
        # 创建HTML下载链接
        html_content = f"""
        <div style="border: 2px dashed #4CAF50; padding: 15px; margin: 10px 0; border-radius: 8px; background-color: #f8fff8;">
            <h4 style="color: #4CAF50; margin-top: 0;">📥 下载准备就绪！</h4>
            <p style="margin-bottom: 10px;">点击下方按钮开始下载文件到您的电脑：</p>
            <a href="{download_url}" 
               download 
               style="display: inline-block; background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                ⬇️ 点击下载文件
            </a>
            <p style="margin-top: 10px; font-size: 12px; color: #666;">
                <strong>下载说明：</strong><br>
                • 文件将直接下载到您的浏览器默认下载目录<br>
                • 下载令牌：{download_token}<br>
                • 如果下载失败，请检查令牌是否正确
            </p>
        </div>
        """
        
        info_text = f"""
**下载链接已生成**

- 下载URL: `{download_url}`
- 下载令牌: `{download_token}`
- 状态: 准备就绪

文件将直接下载到您的电脑，不会经过服务器保存。
"""
        
        return info_text, gr.update(value=html_content, visible=True), gr.update(value=info_text, visible=True)
                
    except Exception as e:
        logger.error(f"下载失败: {e}")
        error_msg = f"**下载失败:** {str(e)}"
        return error_msg, gr.update(visible=False), gr.update(visible=False)


def create_ui():
    """创建Gradio UI界面"""
    global main_args
    
    # 设置主题
    themes = {
        'soft': gr.themes.Soft(),
        'monochrome': gr.themes.Monochrome(),
        'base': gr.themes.Base(),
        'default': gr.themes.Default(),
        'glass': gr.themes.Glass()
    }
    theme = themes.get(main_args.theme, gr.themes.Soft())
    
    with gr.Blocks(
        theme=theme,
        title='HuixiangDou AI Assistant - API Client',
        analytics_enabled=True
    ) as demo:
        
        gr.Markdown("""
        # 🤖 HuixiangDou AI Assistant
        
        **基于API的智能问答系统** | *Powered by HuixiangDou*
        
        ---
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                # 配置面板
                gr.Markdown("### ⚙️ 配置设置")
                
                ui_language = gr.Radio(
                    ["en", "zh_cn"],
                    label="语言设置",
                    value=language,
                    info="选择界面和回复语言"
                )
                
                ui_web_search = gr.Radio(
                    ["no", "yes"],
                    label="网络搜索",
                    value="no",
                    info="是否启用网络搜索功能"
                )
                
                ui_db_name = gr.Textbox(
                    label="数据库名称",
                    placeholder="输入数据库名称",
                    value=current_db_name,
                    info="当前使用的数据库，可直接编辑切换"
                )
                
                ui_btn_switch_db = gr.Button(
                    '↔️ 切换数据库'
                )
                
                # 文件管理
                gr.Markdown("### 📁 知识库管理")
                
                ui_allfiles = gr.TextArea(
                    label="当前知识库文件列表",
                    value=asyncio.run(get_files_list()),
                    lines=8,
                    max_lines=12
                )
                
                files = gr.File(
                    file_count="multiple",
                    label="选择要上传的文件",
                    file_types=[".pdf", ".txt", ".md", ".docx", ".xlsx", ".pptx"]
                )
                
                with gr.Row():
                    ui_file_button = gr.Button('📤 上传文件', variant="primary")
                    ui_refresh_button = gr.Button('🔄 刷新列表')
                
                ui_drop_button = gr.Button('🗑️ 清空知识库', variant="stop")
                
                # 导出功能
                gr.Markdown("### 📊 数据导出")
                ui_export_button = gr.Button('📈 导出图谱数据', variant="secondary")
                ui_export_status = gr.Markdown("点击上方按钮导出当前数据库的图谱数据")
                
                download_token = gr.Textbox(
                    label="下载令牌",
                    placeholder="从导出结果中复制下载令牌",
                    info="用于下载导出的图谱文件"
                )
                ui_download_button = gr.Button('⬇️ 下载导出文件', variant="secondary")
                ui_download_status = gr.Markdown("")
                
                # 下载链接显示区域（初始隐藏）
                download_link_html = gr.HTML(visible=False)
                download_info = gr.Markdown(visible=False)
                
            with gr.Column(scale=2):
                # 聊天界面
                gr.Markdown("### 💬 智能问答")
                
                chatbot = gr.Chatbot(
                    label="对话记录",
                    height=400,
                    show_copy_button=True,
                    bubble_full_width=False
                )
                
                with gr.Row():
                    input_question = gr.Textbox(
                        label="输入问题",
                        placeholder=main_args.placeholder,
                        scale=4,
                        lines=2
                    )
                    run_button = gr.Button('🚀 发送', scale=1, variant="primary")
                
                # 状态显示
                system_state = gr.Markdown(
                    "系统就绪",
                    label="系统状态"
                )
        
        # 事件处理
        ui_language.change(
            fn=on_language_changed,
            inputs=ui_language,
            outputs=system_state
        )
        
        ui_web_search.change(
            fn=on_web_search_changed,
            inputs=ui_web_search,
            outputs=system_state
        )
        
        # ui_db_name.change(
        #     fn=on_db_name_changed,
        #     inputs=ui_db_name,
        #     outputs=system_state
        # ).then(
        #     fn=lambda: asyncio.run(get_files_list()),
        #     outputs=ui_allfiles
        # )
        
        ui_btn_switch_db.click(
            fn=on_db_name_changed,
            inputs=[ui_db_name],
            outputs=system_state
        ).then(
            fn=lambda: asyncio.run(get_files_list()),
            outputs=ui_allfiles
        )
        
        ui_file_button.click(
            fn=add_files,
            inputs=[files],
            outputs=[system_state, ui_allfiles]
        )
        
        ui_refresh_button.click(
            fn=lambda: asyncio.run(get_files_list()),
            outputs=ui_allfiles
        )
        
        ui_drop_button.click(
            fn=drop_db,
            inputs=[],
            outputs=[system_state, ui_allfiles]
        )
        
        ui_export_button.click(
            fn=export_graph_data,
            inputs=[],
            outputs=[ui_export_status, download_token]
        )
        
        # 当下载令牌输入框内容改变时，隐藏之前的下载链接
        download_token.change(
            fn=lambda x: (gr.update(visible=False), gr.update(visible=False)) if x else (gr.update(), gr.update()),
            inputs=[download_token],
            outputs=[download_link_html, download_info]
        )
        
        ui_download_button.click(
            fn=download_export_file,
            inputs=[download_token],
            outputs=[ui_download_status, download_link_html, download_info]
        )
        
        async def chat_wrapper(message, history):
            """聊天功能的包装器"""
            if not message:
                yield "", history
            
            # 转换历史记录格式
            chat_history = []
            if history:
                for i in range(0, len(history), 2):
                    if i+1 < len(history):
                        chat_history.append({
                            "user": history[i][1] if isinstance(history[i], tuple) else str(history[i]),
                            "assistant": history[i+1][1] if isinstance(history[i+1], tuple) else str(history[i+1]),
                            "references": []
                        })
            
            # 流式生成回复
            full_response = ""
            async for response_text in predict(message, chat_history):
                full_response = response_text
                yield "", history + [[message, full_response]]
        
        run_button.click(
            fn=chat_wrapper,
            inputs=[input_question, chatbot],
            outputs=[input_question, chatbot]
        )
        
        # 回车发送消息
        input_question.submit(
            fn=chat_wrapper,
            inputs=[input_question, chatbot],
            outputs=[input_question, chatbot]
        )
    
    return demo


def main():
    """主函数"""
    global main_args, server_base_url
    
    main_args = parse_args()
    server_base_url = main_args.server_url
    
    logger.info("HuixiangDou Gradio UI (API客户端模式)")
    logger.info(f"服务器地址: {server_base_url}")
    logger.info(f"监听端口: {main_args.server_port}")
    
    # 创建UI
    demo = create_ui()
    
    # 启动服务
    demo.launch(
        server_name='0.0.0.0',
        server_port=main_args.server_port,
        share=main_args.share,
        debug=True,
        show_api=False
    )


if __name__ == '__main__':
    main()