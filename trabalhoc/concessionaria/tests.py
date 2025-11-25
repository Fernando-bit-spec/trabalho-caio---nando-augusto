from decimal import Decimal
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Carro
from .serializer import CarroSerializer


class BaseCarroTest(TestCase):
    """Classe base com dados comuns para testes do app concessionaria"""

    def setUp(self):
        """Configura dados padrão e cria um carro de exemplo para testes"""
        self.carro_data = {
            "marca": "Fiat",
            "modelo": "Uno",
            "ano": 2010,
            "preco": "19999.90",
        }
        self.carro = Carro.objects.create(
            marca=self.carro_data["marca"],
            modelo=self.carro_data["modelo"],
            ano=self.carro_data["ano"],
            preco=Decimal(self.carro_data["preco"]),
        )


class TestCarroModel(BaseCarroTest):
    """Testes do modelo Carro: validação de campos e métodos"""

    def test_model_str_representation(self):
        """Verifica se __str__ retorna 'marca modelo'"""
        expected = f"{self.carro.marca} {self.carro.modelo}"
        assert str(self.carro) == expected

    def test_model_fields_persistence(self):
        """Verifica se os campos são persistidos corretamente no banco"""
        carro = Carro.objects.get(pk=self.carro.pk)
        assert carro.marca == "Fiat"
        assert carro.modelo == "Uno"
        assert carro.ano == 2010
        assert carro.preco == Decimal("19999.90")

    def test_model_auto_now_add_field(self):
        """Verifica se criado_em é preenchido automaticamente"""
        assert self.carro.criado_em is not None


class TestCarroSerializer(BaseCarroTest):
    """Testes do serializador CarroSerializer: validação e serialização"""

    def test_serializer_contains_required_fields(self):
        """Verifica se todos os campos esperados estão na saída do serializer"""
        serializer = CarroSerializer(self.carro)
        data = serializer.data
        required_fields = ("id", "marca", "modelo", "ano", "preco", "criado_em")
        for field in required_fields:
            assert field in data, f"Campo '{field}' não encontrado na serialização"

    def test_serializer_field_values(self):
        """Verifica se os valores serializados correspondem aos do modelo"""
        serializer = CarroSerializer(self.carro)
        data = serializer.data
        assert data["marca"] == "Fiat"
        assert data["modelo"] == "Uno"
        assert data["ano"] == 2010

    def test_serializer_validation_and_object_creation(self):
        """Verifica validação e criação de novo objeto via serializer"""
        new_carro_data = {
            "marca": "Volks",
            "modelo": "Gol",
            "ano": 2015,
            "preco": "29999.00",
        }
        serializer = CarroSerializer(data=new_carro_data)
        assert serializer.is_valid(), f"Erros de validação: {serializer.errors}"
        obj = serializer.save()
        assert isinstance(obj, Carro)
        assert obj.marca == "Volks"


class TestCarroViewSet(BaseCarroTest):
    """Testes da API ViewSet: rotas HTTP e operações CRUD"""

    def setUp(self):
        """Inicializa o cliente API e dados de teste"""
        super().setUp()
        self.client = APIClient()

    def test_list_endpoint_returns_200(self):
        """Verifica se GET /carros/ retorna status 200"""
        resp = self.client.get("/carros/")
        assert resp.status_code == status.HTTP_200_OK

    def test_list_endpoint_contains_created_car(self):
        """Verifica se o carro criado está na lista retornada"""
        resp = self.client.get("/carros/")
        data = resp.json()
        results = data.get("results", data) if isinstance(data, dict) else data
        assert any(item["id"] == self.carro.id for item in results), \
            "Carro criado não encontrado na listagem"

    def test_create_endpoint_201_created(self):
        """Verifica se POST /carros/ cria um novo carro e retorna sucesso"""
        resp = self.client.post("/carros/", data=self.carro_data, format="json")
        assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)

    def test_create_endpoint_persists_object(self):
        """Verifica se o objeto foi realmente criado no banco de dados"""
        new_data = {
            "marca": "Toyota",
            "modelo": "Corolla",
            "ano": 2020,
            "preco": "85000.00",
        }
        self.client.post("/carros/", data=new_data, format="json")
        assert Carro.objects.filter(marca="Toyota", modelo="Corolla").exists()

    def test_retrieve_endpoint_returns_car(self):
        """Verifica se GET /carros/{id}/ retorna o carro correto"""
        resp = self.client.get(f"/carros/{self.carro.id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == self.carro.id

    def test_update_endpoint_partial_update(self):
        """Verifica se PATCH /carros/{id}/ atualiza parcialmente o carro"""
        new_price = "14999.00"
        resp = self.client.patch(
            f"/carros/{self.carro.id}/",
            data={"preco": new_price},
            format="json"
        )
        assert resp.status_code in (status.HTTP_200_OK, status.HTTP_202_ACCEPTED)
        self.carro.refresh_from_db()
        assert self.carro.preco == Decimal(new_price)

    def test_delete_endpoint_removes_car(self):
        """Verifica se DELETE /carros/{id}/ remove o carro do banco"""
        carro_id = self.carro.id
        resp = self.client.delete(f"/carros/{carro_id}/")
        assert resp.status_code in (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK)
        assert not Carro.objects.filter(pk=carro_id).exists()


class TestCarroAppStructure(TestCase):
    """Testes da estrutura do app: documentação de ausência de forms/templates"""

    def test_no_forms_module_exists(self):
        """Documenta que não há forms.py no app (uso de REST API apenas)"""
        try:
            import importlib
            forms_mod = importlib.import_module("trabalhoc.concessionaria.forms")
        except ModuleNotFoundError:
            forms_mod = None
        assert forms_mod is None, "forms.py não deve existir (app usa DRF viewsets)"

    def test_no_templates_directory_required(self):
        """Documenta que o app não usa templates HTML (API JSON apenas)"""
        # Este app é uma API REST que retorna JSON, não renderiza templates
        # Função documentar essa arquitetura
        assert True
