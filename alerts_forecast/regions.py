"""Shared, explicit regional identities for the dashboard, map and bot."""
REGISTRY=[
('UA-71','Cherkaska oblast','Черкаська'),('UA-74','Chernihivska oblast','Чернігівська'),
('UA-77','Chernivetska oblast','Чернівецька'),('UA-12','Dnipropetrovska oblast','Дніпропетровська'),
('UA-14','Donetska oblast','Донецька'),('UA-26','Ivano-Frankivska oblast','Івано-Франківська'),
('UA-63','Kharkivska oblast','Харківська'),('UA-65','Khersonska oblast','Херсонська'),
('UA-68','Khmelnytska oblast','Хмельницька'),('UA-35','Kirovohradska oblast','Кіровоградська'),
('UA-30','Kyiv City','м. Київ'),('UA-32','Kyivska oblast','Київська'),
('UA-09','Luhanska oblast','Луганська'),('UA-46','Lvivska oblast','Львівська'),
('UA-48','Mykolaivska oblast','Миколаївська'),('UA-51','Odeska oblast','Одеська'),
('UA-53','Poltavska oblast','Полтавська'),('UA-56','Rivnenska oblast','Рівненська'),
('UA-59','Sumska oblast','Сумська'),('UA-61','Ternopilska oblast','Тернопільська'),
('UA-05','Vinnytska oblast','Вінницька'),('UA-07','Volynska oblast','Волинська'),
('UA-21','Zakarpatska oblast','Закарпатська'),('UA-23','Zaporizka oblast','Запорізька'),
('UA-18','Zhytomyrska oblast','Житомирська'),
('UA-43','Autonomous Republic of Crimea','АР Крим'),('UA-40','Sevastopol City','м. Севастополь')]
LABELS={name:uk for iso,name,uk in REGISTRY}
ISOS={name:iso for iso,name,uk in REGISTRY}
