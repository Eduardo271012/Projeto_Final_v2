from sqlalchemy import select

from database import db_session, Usuario


def criar_usuario():
    email_admin = "admin@empresa.com.br"

    admin = db_session.execute(
        select(Usuario).where(Usuario.email == email_admin)
    ).scalar_one_or_none()

    if admin is None:
        admin = Usuario(
            nome="Administrador",
            email=email_admin,
            papel="admin",
        )
        admin.set_password("quarks26")
        db_session.add(admin)
    else:
        admin.papel = "admin"
        admin.set_password("quarks26")

    db_session.commit()
    print("Administrador criado/atualizado com sucesso.")


if __name__ == "__main__":
    criar_usuario()
