from source_code.constants import PRIVILEGES
from source_code.data import db_session
from source_code.data.privileges import Privileges


if __name__ == '__main__':
    db_session.global_init("source_code/db/mars_explorer.db")
    session = db_session.create_session()

    privilege = Privileges()
    privilege.privilege_id = PRIVILEGES['contributor']
    privilege.name = 'Contributor'
    privilege.is_displaying = True
    session.add(privilege)

    session.commit()
