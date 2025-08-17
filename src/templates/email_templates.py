"""Email templates for password reset functionality."""

from typing import Dict, Any
from src.core.config import settings


class EmailTemplates:
    """Email templates for various notifications."""
    
    @staticmethod
    def password_reset_template(nama: str, reset_link: str) -> Dict[str, Any]:
        return {
            "subject": "Reset Kata Sandi - Yayasan Baitul Muslim Lampung Timur",
            "htmlContent": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Reset Kata Sandi - Yayasan Baitul Muslim</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f8fafc;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 12px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #e2e8f0;
                        padding-bottom: 20px;
                    }}
                    .logo {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #1e40af;
                        margin-bottom: 5px;
                    }}
                    .subtitle {{
                        font-size: 14px;
                        color: #64748b;
                    }}
                    .content {{
                        line-height: 1.6;
                        color: #334155;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e2e8f0;
                        font-size: 12px;
                        color: #64748b;
                        text-align: center;
                    }}
                    .warning {{
                        background-color: #fef3c7;
                        border-left: 4px solid #f59e0b;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .btn {{
                        display: inline-block;
                        padding: 12px 28px;
                        background-color: #1e40af;
                        color: #ffffff;
                        font-size: 14px;
                        font-weight: 600;
                        text-decoration: none;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🕌 Yayasan Baitul Muslim</div>
                        <div class="subtitle">Lembaga Pendidikan Islam Terpadu - Lampung Timur</div>
                    </div>

                    <div class="content">
                        <h2 style="color: #1e40af;">Permintaan Reset Kata Sandi</h2>
                        <p>Yth. <strong>{nama}</strong>,</p>

                        <p>Kami menerima permintaan untuk mengatur ulang kata sandi akun Anda di sistem Yayasan Baitul Muslim Lampung Timur. Jika Anda tidak melakukan permintaan ini, mohon abaikan email ini.</p>

                        <p>Untuk mengatur ulang kata sandi Anda, silakan klik tombol di bawah ini:</p>

                        <div style="text-align: center;">
                            <a href="{reset_link}" class="btn">
                                🔑 Reset Kata Sandi
                            </a>
                        </div>

                        <p>Atau salin dan tempel tautan berikut ke browser Anda:</p>
                        <p style="word-break: break-all; background-color: #f1f5f9; padding: 12px; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 13px;">
                            {reset_link}
                        </p>

                        <div class="warning">
                            <strong>⚠️ Perhatian Penting:</strong>
                            <ul style="margin: 10px 0;">
                                <li>Tautan ini hanya berlaku selama <strong>1 jam</strong></li>
                                <li>Tautan hanya dapat digunakan <strong>satu kali</strong></li>
                                <li>Jangan bagikan tautan ini kepada siapa pun demi keamanan akun Anda</li>
                            </ul>
                        </div>

                        <p><strong>Butuh bantuan?</strong> Silakan hubungi administrator yayasan atau tim IT support kami.</p>
                    </div>

                    <div class="footer">
                        <p>Email ini dikirim secara otomatis, mohon tidak membalas email ini.</p>
                        <p>© 2025 Yayasan Baitul Muslim Lampung Timur. Hak cipta dilindungi undang-undang.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "textContent": f"""
            Reset Kata Sandi - Yayasan Baitul Muslim Lampung Timur

            Yth. {nama},

            Kami menerima permintaan untuk mengatur ulang kata sandi akun Anda di sistem Yayasan Baitul Muslim Lampung Timur. Jika Anda tidak melakukan permintaan ini, mohon abaikan email ini.

            Untuk mengatur ulang kata sandi, silakan buka tautan berikut:
            {reset_link}

            PERHATIAN PENTING:
            - Tautan ini hanya berlaku selama 1 jam
            - Tautan hanya dapat digunakan satu kali
            - Jangan bagikan tautan ini kepada siapa pun demi keamanan akun Anda

            Butuh bantuan? Silakan hubungi administrator sekolah atau tim IT support.

            Email ini dikirim secara otomatis, mohon tidak membalas email ini.

            © 2025 Yayasan Baitul Muslim Lampung Timur. Hak cipta dilindungi undang-undang.
            """
        }

    
    @staticmethod
    def password_reset_success_template(nama: str) -> Dict[str, Any]:
        """
        Template untuk konfirmasi password reset berhasil.
        
        Args:
            nama: Nama lengkap user
            
        Returns:
            Email template data untuk Brevo API
        """
        return {
            "subject": "Kata Sandi Berhasil Direset - Yayasan Baitul Muslim Lampung Timur",
            "htmlContent": f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Kata Sandi Berhasil Direset - Yayasan Baitul Muslim</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f8fafc;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 12px;
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        border-bottom: 2px solid #e2e8f0;
                        padding-bottom: 20px;
                    }}
                    .logo {{
                        font-size: 26px;
                        font-weight: bold;
                        color: #1e40af;
                        margin-bottom: 5px;
                    }}
                    .subtitle {{
                        font-size: 14px;
                        color: #64748b;
                    }}
                    .content {{
                        line-height: 1.6;
                        color: #334155;
                    }}
                    .success {{
                        background-color: #d1fae5;
                        border-left: 4px solid #10b981;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .security-tips {{
                        background-color: #f0f9ff;
                        border-left: 4px solid #0ea5e9;
                        padding: 15px;
                        border-radius: 5px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #e2e8f0;
                        font-size: 12px;
                        color: #64748b;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">🕌 Yayasan Baitul Muslim</div>
                        <div class="subtitle">Lembaga Pendidikan Islam Terpadu - Lampung Timur</div>
                    </div>
                    
                    <div class="content">
                        <h2 style="color: #1e40af;">Kata Sandi Berhasil Direset</h2>
                        <p>Yth. <strong>{nama}</strong>,</p>
                        
                        <div class="success">
                            <strong>✅ Kata sandi Anda telah berhasil direset!</strong>
                        </div>
                        
                        <p>Kata sandi akun Anda di sistem Yayasan Baitul Muslim Lampung Timur telah berhasil diubah. Anda sekarang dapat masuk kembali menggunakan kata sandi baru Anda.</p>
                        
                        <p>⚠️ <strong>Jika Anda tidak melakukan perubahan kata sandi ini</strong>, segera hubungi administrator yayasan atau tim IT support kami untuk keamanan akun Anda.</p>
                        
                        <div class="security-tips">
                            <p><strong>💡 Tips Keamanan Akun:</strong></p>
                            <ul style="margin: 10px 0;">
                                <li>Gunakan kata sandi yang kuat dan unik (minimal 8 karakter dengan kombinasi huruf, angka, dan simbol)</li>
                                <li>Jangan bagikan kata sandi kepada siapa pun, termasuk rekan kerja</li>
                                <li>Keluar dari sistem setelah selesai menggunakan, terutama di komputer bersama</li>
                                <li>Ubah kata sandi secara berkala untuk menjaga keamanan</li>
                            </ul>
                        </div>

                        <p><strong>Butuh bantuan?</strong> Silakan hubungi administrator yayasan atau tim IT support kami jika Anda mengalami kesulitan.</p>
                    </div>
                    
                    <div class="footer">
                        <p>Email ini dikirim secara otomatis, mohon tidak membalas email ini.</p>
                        <p>© 2025 Yayasan Baitul Muslim Lampung Timur. Hak cipta dilindungi undang-undang.</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            "textContent": f"""
            Kata Sandi Berhasil Direset - Yayasan Baitul Muslim Lampung Timur
            
            Yth. {nama},
            
            ✅ Kata sandi Anda telah berhasil direset!
            
            Kata sandi akun Anda di sistem Yayasan Baitul Muslim Lampung Timur telah berhasil diubah. Anda sekarang dapat masuk kembali menggunakan kata sandi baru Anda.
            
            ⚠️ Jika Anda tidak melakukan perubahan kata sandi ini, segera hubungi administrator yayasan atau tim IT support kami untuk keamanan akun Anda.
            
            Tips Keamanan Akun:
            - Gunakan kata sandi yang kuat dan unik (minimal 8 karakter dengan kombinasi huruf, angka, dan simbol)
            - Jangan bagikan kata sandi kepada siapa pun, termasuk rekan kerja
            - Keluar dari sistem setelah selesai menggunakan, terutama di komputer bersama
            - Ubah kata sandi secara berkala untuk menjaga keamanan
            
            Butuh bantuan? Silakan hubungi administrator yayasan atau tim IT support kami jika Anda mengalami kesulitan.
            
            Email ini dikirim secara otomatis, mohon tidak membalas email ini.
            
            © 2025 Yayasan Baitul Muslim Lampung Timur. Hak cipta dilindungi undang-undang.
            """
        }